import itertools
import logging
import os
import sys
import tempfile
import click
import solv
import xdg

CACHEDIR = os.path.join(xdg.XDG_CACHE_HOME, "depchase")

logger = logging.getLogger("depchase")

class Repo(object):
    def __init__(self, name, baseurl):
        self.name = name
        self.baseurl = baseurl
        self.handle = None
        self.cookie = None
        self.extcookie = None

    @staticmethod
    def calc_cookie_fp(fp):
        chksum = solv.Chksum(solv.REPOKEY_TYPE_SHA256)
        chksum.add("1.1")
        chksum.add_fp(fp)
        return chksum.raw()

    @staticmethod
    def calc_cookie_ext(f, cookie):
        chksum = solv.Chksum(solv.REPOKEY_TYPE_SHA256)
        chksum.add("1.1")
        chksum.add(cookie)
        chksum.add_fstat(f.fileno())
        return chksum.raw()

    def cachepath(self, ext=None):
        path = self.name.replace(".", "_")
        if ext:
            path = "{}-{}.solvx".format(path, ext)
        else:
            path = "{}.solv".format(path)
        return os.path.join(CACHEDIR, path.replace("/", "_"))

    def usecachedrepo(self, ext, mark=False):
        try:
            repopath = self.cachepath(ext)
            f = open(repopath, "rb")
            f.seek(-32, os.SEEK_END)
            fcookie = f.read(32)
            if len(fcookie) != 32:
                return False
            cookie = self.extcookie if ext else self.cookie
            if cookie and fcookie != cookie:
                return False
            if not ext:
                f.seek(-32 * 2, os.SEEK_END)
                fextcookie = f.read(32)
                if len(fextcookie) != 32:
                    return False
            f.seek(0)
            f = solv.xfopen_fd(None, f.fileno())
            flags = 0
            if ext:
                flags = solv.Repo.REPO_USE_LOADING | solv.Repo.REPO_EXTEND_SOLVABLES
                if ext != "DL":
                    flags |= solv.Repo.REPO_LOCALPOOL
            if not self.handle.add_solv(f, flags):
                return False
            if not ext:
                self.cookie = fcookie
                self.extcookie = fextcookie
            if mark:
                # no futimes in python?
                try:
                    os.utime(repopath, None)
                except Exception:
                    pass
        except IOError:
            return False
        return True

    def writecachedrepo(self, ext, repodata=None):
        tmpname = None
        try:
            if not os.path.isdir(CACHEDIR):
                os.mkdir(CACHEDIR, 0o755)
            fd, tmpname = tempfile.mkstemp(prefix=".newsolv-", dir=CACHEDIR)
            os.fchmod(fd, 0o444)
            f = os.fdopen(fd, "wb+")
            f = solv.xfopen_fd(None, f.fileno())
            if not repodata:
                self.handle.write(f)
            elif ext:
                repodata.write(f)
            else:
                # rewrite_repos case, do not write stubs
                self.handle.write_first_repodata(f)
            f.flush()
            if not ext:
                if not self.extcookie:
                    self.extcookie = self.calc_cookie_ext(f, self.cookie)
                f.write(self.extcookie)
            if not ext:
                f.write(self.cookie)
            else:
                f.write(self.extcookie)
            f.close
            if self.handle.iscontiguous():
                # switch to saved repo to activate paging and save memory
                nf = solv.xfopen(tmpname)
                if not ext:
                    # main repo
                    self.handle.empty()
                    flags = solv.Repo.SOLV_ADD_NO_STUBS
                    if repodata:
                        # rewrite repos case, recreate stubs
                        flags = 0
                    if not self.handle.add_solv(nf, flags):
                        sys.exit("internal error, cannot reload solv file")
                else:
                    # extension repodata
                    # need to extend to repo boundaries, as this is how
                    # repodata.write() has written the data
                    repodata.extend_to_repo()
                    flags = solv.Repo.REPO_EXTEND_SOLVABLES
                    if ext != "DL":
                        flags |= solv.Repo.REPO_LOCALPOOL
                    repodata.add_solv(nf, flags)
            os.rename(tmpname, self.cachepath(ext))
        except (OSError, IOError):
            if tmpname:
                os.unlink(tmpname)

    def load(self, pool):
        assert not self.handle
        self.handle = pool.add_repo(self.name)
        self.handle.appdata = self
        f = self.download("repodata/repomd.xml", False, None)
        if not f:
            self.handle.free(True)
            self.handle = None
            return False
        self.cookie = self.calc_cookie_fp(f)
        if self.usecachedrepo(None, True):
            return True
        self.handle.add_repomdxml(f)
        fname, fchksum = self.find("primary")
        if not fname:
            return False
        f = self.download(fname, True, fchksum)
        if not f:
            return False
        self.handle.add_rpmmd(f, None)
        self.add_exts()
        self.writecachedrepo(None)
        # Must be called after writing the repo
        self.handle.create_stubs()
        return True

    def download(self, fname, uncompress, chksum):
        f = open("{}/{}".format(self.baseurl, fname))
        return solv.xfopen_fd(fname if uncompress else None, f.fileno())

    def find(self, what):
        di = self.handle.Dataiterator_meta(solv.REPOSITORY_REPOMD_TYPE, what, solv.Dataiterator.SEARCH_STRING)
        di.prepend_keyname(solv.REPOSITORY_REPOMD)
        for d in di:
            dp = d.parentpos()
            filename = dp.lookup_str(solv.REPOSITORY_REPOMD_LOCATION)
            chksum = dp.lookup_checksum(solv.REPOSITORY_REPOMD_CHECKSUM)
            if filename:
                if not chksum:
                    print("No {} file checksum!".format(filename))
                return filename, chksum
        return None, None

    def add_ext_keys(self, ext, repodata, handle):
        if ext == "FL":
            repodata.add_idarray(handle, solv.REPOSITORY_KEYS, solv.SOLVABLE_FILELIST)
            repodata.add_idarray(handle, solv.REPOSITORY_KEYS, solv.REPOKEY_TYPE_DIRSTRARRAY)
        else:
            raise NotImplementedError

    def add_ext(self, repodata, what, ext):
        filename, chksum = self.find(what)
        if not filename:
            return
        handle = repodata.new_handle()
        repodata.set_poolstr(handle, solv.REPOSITORY_REPOMD_TYPE, what)
        repodata.set_str(handle, solv.REPOSITORY_REPOMD_LOCATION, filename)
        repodata.set_checksum(handle, solv.REPOSITORY_REPOMD_CHECKSUM, chksum)
        self.add_ext_keys(ext, repodata, handle)
        repodata.add_flexarray(solv.SOLVID_META, solv.REPOSITORY_EXTERNAL, handle)

    def add_exts(self):
        repodata = self.handle.add_repodata()
        self.add_ext(repodata, "filelists", "FL")
        repodata.internalize()

    def load_ext(self, repodata):
        repomdtype = repodata.lookup_str(solv.SOLVID_META, solv.REPOSITORY_REPOMD_TYPE)
        if repomdtype == "filelists":
            ext = "FL"
        else:
            assert False
        if self.usecachedrepo(ext):
            return True
        filename = repodata.lookup_str(solv.SOLVID_META, solv.REPOSITORY_REPOMD_LOCATION)
        filechksum = repodata.lookup_checksum(solv.SOLVID_META, solv.REPOSITORY_REPOMD_CHECKSUM)
        f = self.download(filename, True, filechksum)
        if not f:
            return False
        if ext == "FL":
            self.handle.add_rpmmd(f, "FL", solv.Repo.REPO_USE_LOADING | solv.Repo.REPO_EXTEND_SOLVABLES | solv.Repo.REPO_LOCALPOOL)
        self.writecachedrepo(ext, repodata)
        return True

    def updateaddedprovides(self, addedprovides):
        if self.handle.isempty():
            return
        # make sure there's just one real repodata with extensions
        repodata = self.handle.first_repodata()
        if not repodata:
            return
        oldaddedprovides = repodata.lookup_idarray(solv.SOLVID_META, solv.REPOSITORY_ADDEDFILEPROVIDES)
        if not set(addedprovides) <= set(oldaddedprovides):
            for id in addedprovides:
                repodata.add_idarray(solv.SOLVID_META, solv.REPOSITORY_ADDEDFILEPROVIDES, id)
            repodata.internalize()
            self.writecachedrepo(None, repodata)

def load_stub(repodata):
    repo = repodata.repo.appdata
    if repo:
        return repo.load_ext(repodata)
    return False

def setup_pool(arch=None):
    pool = solv.Pool()
    #pool.set_debuglevel(2)
    pool.setarch(arch)
    pool.set_loadcallback(load_stub)

    base = Repo("base", "/home/brain/tmp/26_Alpha/x86_64")
    base_src = Repo("base-source", "/home/brain/tmp/26_Alpha/source")
    override = Repo("base-override", "/home/brain/tmp/foo/binaries")
    override_src = Repo("base-override-source", "/home/brain/tmp/foo/sources")
    repos = [base, base_src, override, override_src]
    for repo in repos:
        assert repo.load(pool)
        if repo.name.endswith("-override"):
            repo.handle.priority = 99

    addedprovides = pool.addfileprovides_queue()
    if addedprovides:
        for repo in repos:
            repo.updateaddedprovides(addedprovides)

    pool.createwhatprovides()

    return pool

def fix_deps(pool):
    # Definitely ugly, but world is not without broken dependencies
    for s in pool.solvables_iter():
        deps = s.lookup_deparray(solv.SOLVABLE_REQUIRES)
        modified = False
        for dep in deps[:]:
            if dep.str() in ("gnu-efi = 3.0w", "gnu-efi-devel = 3.0w", "pkgconfig(botan-1.10)"):
                deps.remove(dep)
                modified = True
        if modified:
            # XXX: use once will be available in libsolv
            #s.set_deparray(solv.SOLVABLE_REQUIRES, deps)
            s.unset(solv.SOLVABLE_REQUIRES)
            for dep in deps:
                s.add_deparray(solv.SOLVABLE_REQUIRES, dep)

def solve(solver, pkgnames, selfhost=False):
    pool = solver.pool

    jobs = []
    # Initial jobs, no conflicting packages
    for n in pkgnames:
        sel = pool.select(n, solv.Selection.SELECTION_NAME | solv.Selection.SELECTION_DOTARCH)
        assert not sel.isempty()
        jobs += sel.jobs(solv.Job.SOLVER_INSTALL)
    problems = solver.solve(jobs)
    assert not problems

    candq = solver.transaction().newpackages()

    if not selfhost:
        return set(candq), None

    # We have to =(
    fix_deps(pool)

    # Hack-ish, but we have no way to match binary against sources
    srcrepo_map = {r.name: None for r in pool.repos if not r.name.endswith("-source")}
    for r in pool.repos:
        if not r.name.endswith("-source"):
            continue
        srcrepo_map[r.name[:-7]] = r
    assert None not in srcrepo_map.values()

    # We already solved runtime requires, no need to do that twice
    selfhosting = set()
    selfhosting_srcs = set()
    # We will store text-based view of processed srcs for better performance
    srcs_done = set()
    while candq:
        jobs = [pool.Job(solv.Job.SOLVER_INSTALL | solv.Job.SOLVER_SOLVABLE | solv.Job.SOLVER_WEAK, p.id) for p in candq]
        solver.solve(jobs)
        # We are interested to operate only on really new packages below
        newpkgs = set(solver.transaction().newpackages()) - selfhosting
        for p in newpkgs.copy():
            if p.arch in ("src", "nosrc"):
                srcs_done.add(str(p))
                selfhosting_srcs.add(p)
                newpkgs.remove(p)
                continue
        selfhosting |= newpkgs

        # SOLVER_FAVOR packages which we already solved which will help us to get small dependency chain
        pool.setpooljobs(pool.getpooljobs() + [pool.Job(solv.Job.SOLVER_FAVOR | solv.Job.SOLVER_SOLVABLE, p.id) for p in newpkgs])

        # In new queue only non-solvables are left
        ncandq = [p for p in candq if solver.get_decisionlevel(p.id) <= 0]
        if ncandq == candq:
            # At this point, nothing can be resolved anymore, so let's show problems
            for p in candq:
                job = pool.Job(solv.Job.SOLVER_INSTALL | solv.Job.SOLVER_SOLVABLE, p.id)
                problems = solver.solve([job])
                # In some cases, even solvable jobs are disabled
                # https://github.com/openSUSE/libsolv/issues/204
                #assert not problems
                for problem in problems:
                    print(problem)
            sys.exit(1)
        candq = ncandq

        srcs_queued = set(str(p) for p in candq if p.arch in ("src", "nosrc"))
        for p in newpkgs:
            s = p.lookup_sourcepkg()[:-4]
            if s in srcs_done or s in srcs_queued:
                continue
            # Let's try to find corresponding source
            sel = pool.select(s, solv.Selection.SELECTION_CANON | solv.Selection.SELECTION_SOURCE_ONLY)
            sel.filter(srcrepo_map[p.repo.name].Selection())
            assert not sel.isempty()
            solvables = sel.solvables()
            assert len(solvables) == 1
            src = solvables[0]
            candq.append(src)

    return selfhosting, selfhosting_srcs

@click.group()
@click.option("-a", "--arch", default=None,
              help="Specify the CPU architecture.")
@click.option("-v", "--verbose", count=True)
@click.pass_context
def cli(ctx, arch, verbose):
    ctx.obj["arch"] = arch
    ctx.obj["verbose"] = verbose
    log_conf = {}
    if verbose == 1:
        log_conf["level"] = logging.INFO
    elif verbose > 1:
        log_conf["level"] = logging.DEBUG
    logging.basicConfig(**log_conf)

@cli.command()
@click.argument("pkgnames", nargs=-1)
@click.option("--recommends/--no-recommends", default=False,
              help="Do not process optional (aka weak) dependencies.")
@click.option("--hint", multiple=True,
              help="""
Specify a package to have higher priority when more than one package could
satisfy a dependency. This option may be specified multiple times.

For example, it is recommended to use --hint=glibc-minimal-langpack.
""")
@click.option("--selfhost", is_flag=True,
              help="Look up the build dependencies as well.")
@click.pass_context
def resolve(ctx, pkgnames, recommends, hint, selfhost):
    pool = setup_pool(ctx.obj["arch"])

    # Set up initial hints
    favorq = []
    for n in hint:
        sel = pool.select(n, solv.Selection.SELECTION_NAME)
        favorq += sel.jobs(solv.Job.SOLVER_FAVOR)
    pool.setpooljobs(favorq)

    solver = pool.Solver()
    if not recommends:
        # Ignore weak deps
        solver.set_flag(solv.Solver.SOLVER_FLAG_IGNORE_RECOMMENDED, 1)

    binary, source = solve(solver, pkgnames, selfhost=selfhost)
    for p in itertools.chain(binary, source or ()):
        print(p)

if __name__ == "__main__":
    cli(obj={})
