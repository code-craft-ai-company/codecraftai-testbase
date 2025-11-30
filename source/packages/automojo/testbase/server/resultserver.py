"""
    .. module:: automojo.testbase.server.resultserver
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: Module for resultserver.

    .. moduleauthor:: Myron Walker <myron.walker@gmail.com>
"""

__author__ = "Myron Walker"
__copyright__ = "Copyright 2025, Automation Mojo LLC"
__credits__ = []




from typing import Dict, Optional, Tuple, Type, Union

import abc
import contextlib
import datetime
import email.utils
import html
import io
import json
import os
import posixpath
import shutil
import socket
import sys
import urllib


from http import HTTPStatus

from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer

from automojo.xmodules.xlogging.enhancedloggers import getEnhancedLogger

from automojo.runtime.runtimevariables import RuntimeVariables, RuntimeVariablesDesc

logger = getEnhancedLogger()


SUPPORTED_BUG_SERVERS = ["JIRA"]

class BugServerInterface(abc.ABC):
    """
        An interface for a bug server.
    """

    def __init__(self, server_type: str, server_endpoint: str, projects: str, team: str, username: str, token: str):
        self._server_type = server_type
        self._server_endpoint = server_endpoint
        self._proejcts = projects
        self._team = team
        self._username = username
        self._token = token
        return

    @property
    def projects(self) -> str:
        return self._proejcts
    
    @property
    def server_type(self) -> str:
        return self._server_type

    @property
    def server_endpoint(self) -> str:
        return self._server_endpoint

    @property
    def team(self) -> str:
        return self._team

    @property
    def username(self) -> str:
        return self._username

    @property
    def token(self) -> str:
        return self._token
    
    @abc.abstractmethod
    def create_issue(self, title: str, runid: str, automation_pod: str,
                     pipeline_info: Optional[Dict[str, str]]=None, job_info: Optional[Dict[str, str]]=None,
                     build_info: Optional[Dict[str, str]]=None, failure_info: Optional[Dict[str, str]]=None) -> str:
        """
            Create an issue in the bug server.
        """
        pass

    @abc.abstractmethod
    def search_issues(self, query: str) -> str:
        """
            Search for issues in the bug server.
        """
        pass
    
    @abc.abstractmethod
    def update_issue(self, issue_id: str, issue_data: dict):
        """
            Update an issue in the bug server.
        """
        pass


class BugServerInterfaceForJira(BugServerInterface):
    """
        A bug server interface for JIRA.
    """

    def __init__(self, server_type: str, server_endpoint: str, projects: str, team: str, username: str, token: str):
        super().__init__(server_type, server_endpoint, projects, team, username, token)
        return

    def create_issue(self, title: str, runid: str, automation_pod: str,
                     pipeline_info: Optional[Dict[str, str]]=None, job_info: Optional[Dict[str, str]]=None,
                     build_info: Optional[Dict[str, str]]=None, failure_info: Optional[Dict[str, str]]=None) -> str:
        """
            Create an issue in the bug server.
        """
        # Implement the create issue logic here
        return

    def search_issues(self, query: str) -> str:
        """
            Search for issues in the bug server.
        """
        # Implement the search logic here
        return
    
    def update_issue(self, issue_id: str, issue_data: dict):
        """
            Update an issue in the bug server.
        """
        # Implement the update issue logic here
        return


def try_create_bug_server_interface_from_environment() -> Union[None, 'BugServerInterface']:
    """
        Construct a BugServerInterface from the environment.
    """
    server_iface = None

    environ = os.environ

    server_type: str = None
    server_endpoint: str = None
    projects: str = None
    team: str = None
    username: str = None
    token: str = None

    server_type = RuntimeVariables.AM_BUG_SERVER_TYPE.upper()

    while server_type is not None: # Setup a breakout pipeline

        if server_type not in SUPPORTED_BUG_SERVERS:
            warn_msg = f"Unknown bug server type: {server_type}"
            logger.warning(warn_msg)
            break

        if RuntimeVariables.AM_BUG_SERVER_ENDPOINT is None:
            warn_msg = f"The Bug Server {RuntimeVariablesDesc.AM_BUG_SERVER_ENDPOINT.name} variable must be set."
            logger.warning(warn_msg)
            break

        server_endpoint = environ[RuntimeVariables.AM_BUG_SERVER_ENDPOINT]

        if RuntimeVariables.AM_BUG_PROJECTS is None:
            warn_msg = f"The Bug Server {RuntimeVariablesDesc.AM_BUG_PROJECTS.name} variable must be set."
            logger.warning(warn_msg)
            break

        projects = environ[RuntimeVariables.AM_BUG_PROJECTS]
        
        if RuntimeVariables.AM_BUG_TEAM is None:
            warn_msg = f"The Bug Server {RuntimeVariablesDesc.AM_BUG_TEAM.name} variable must be set."
            logger.warning(warn_msg)
            break

        team = environ[RuntimeVariables.AM_BUG_TEAM]

        if RuntimeVariables.AM_BUG_USERNAME is None:
            warn_msg = f"The Bug Server {RuntimeVariablesDesc.AM_BUG_USERNAME.name} variable must be set."
            logger.warning(warn_msg)
            break

        username = environ[RuntimeVariables.AM_BUG_USERNAME]

        if RuntimeVariables.AM_BUG_TOKEN is None:
            warn_msg = f"The Bug Server {RuntimeVariablesDesc.AM_BUG_TOKEN} variable must be set."
            logger.warning(warn_msg)
            break

        token = environ[RuntimeVariables.AM_BUG_TOKEN]

        # If we have all the required information to construct the server interface, create it and
        # assign it to the 'server_iface' in order to return it.
        if server_type == "JIRA":
            server_iface = BugServerInterfaceForJira(
                server_type=server_type,
                server_endpoint=server_endpoint,
                projects=projects,
                team=team,
                username=username,
                token=token
            )

        break # Always exit this 'while True' pipeline after one time through

    return server_iface


class TestResultRequestHandler(SimpleHTTPRequestHandler):
    """
        A web request handler which reclassifies file types of test results as text so the browser can
        properly display them.
    """

    def __init__(self, *args, directory=None, bug_server: BugServerInterface=None,**kwargs):
        self._no_sniff_header = False
        self._bug_server = bug_server

        super().__init__(*args, directory=directory, **kwargs)
        return

    def do_GET(self):
        """Serve a GET request."""
        if self.path.startswith('/api'):
            self.handle_api_get(self.path)
        else:
            f = self.send_head()
            if f:
                try:
                    self.copyfile(f, self.wfile)
                finally:
                    f.close()

    def do_POST(self):
        """Serve a POST request."""
        
        if self.path.startswith('/api'):
            self.handle_api_post(self.path)
        else:
            self.send_error(HTTPStatus.BAD_REQUEST, "INVALID REQUEST")

        return
    
    def do_PUT(self):
        """Serve a PUT request."""
        
        if self.path.startswith('/api'):
            self.handle_api_put(self.path)

        return

    def copyfile(self, source, outputfile):
        """
            Copy all data between two file objects.

            The ``source`` argument must be a file object open for reading and
            ``outputfile`` must be a file object open for writing.  The default
            implementation simply delegates to :func:`shutil.copyfileobj`.
        """
        shutil.copyfileobj(source, outputfile)

    def handle_api_get(self, path: str):
        """Handle GET requests to the /api endpoint."""

        
        if path == "/api/v1/environment":
            response = {
                RuntimeVariablesDesc.AM_BUG_SERVER_TYPE.name: self._bug_server.server_type,
                RuntimeVariablesDesc.AM_BUG_SERVER_ENDPOINT.name: self._bug_server.server_endpoint,
                RuntimeVariablesDesc.AM_BUG_PROJECTS.name: self._bug_server.projects,
                RuntimeVariablesDesc.AM_BUG_TEAM.name: self._bug_server.team,
                RuntimeVariablesDesc.AM_BUG_USERNAME.name: self._bug_server.username,
                RuntimeVariablesDesc.AM_BUG_TOKEN.name: self._bug_server.token
            }

            rcontent = json.dumps(response).encode('utf-8')

            self.send_response(HTTPStatus.OK)
            self.send_header("Content-type", "application/json")
            self.send_header("Content-Length", str(len(rcontent)))
            self.try_send_bug_server_header()
            self.end_headers()

            self.wfile.write(rcontent.encode('utf-8'))
            
        else:
            # Handle other API paths
            self.send_response(HTTPStatus.NOT_FOUND)
            self.send_header("Content-type", "text/html")
            self.try_send_bug_server_header()
            self.end_headers()
            
            # Example response for unsupported path

        return

    def handle_api_post(self, path: str):
        """Handle POST requests to the /api endpoint."""
        
        # Implement your API logic here
        self.send_response(HTTPStatus.NOT_IMPLEMENTED)
        self.send_header("Content-type", "text/html")
        self.try_send_bug_server_header()
        self.end_headers()
        
        rcontent = f"POST not supported for path: {path}"

        self.wfile.write(rcontent.encode('utf-8'))

        return

    def handle_api_put(self, path: str):
        """Handle PUT requests to the /api endpoint."""
        
        # Implement your API logic here
        self.send_response(HTTPStatus.NOT_IMPLEMENTED)
        self.send_header("Content-type", "text/html")
        self.try_send_bug_server_header()
        self.end_headers()
        
        rcontent = f"PUT not supported for path: {path}"

        self.wfile.write(rcontent.encode('utf-8'))
        
        return

    def list_directory(self, path):
        """Helper to produce a directory listing (absent index.html).

        Return value is either a file object, or None (indicating an
        error).  In either case, the headers are sent, making the
        interface the same as for send_head().

        """
        try:
            list = os.listdir(path)
        except OSError:
            self.send_error(
                HTTPStatus.NOT_FOUND,
                "No permission to list directory")
            return None
        list.sort(key=lambda a: a.lower())
        r = []
        try:
            displaypath = urllib.parse.unquote(self.path,
                                               errors='surrogatepass')
        except UnicodeDecodeError:
            displaypath = urllib.parse.unquote(self.path)
        displaypath = html.escape(displaypath, quote=False)
        enc = sys.getfilesystemencoding()
        title = f'Directory listing for {displaypath}'
        r.append('<!DOCTYPE HTML>')
        r.append('<html lang="en">')
        r.append('<head>')
        r.append(f'<meta charset="{enc}">')
        r.append(f'<title>{title}</title>\n</head>')
        r.append(f'<body>\n<h1>{title}</h1>')
        r.append('<hr>\n<ul>')
        for name in list:
            fullname = os.path.join(path, name)
            displayname = linkname = name
            # Append / for directories or @ for symbolic links
            if os.path.isdir(fullname):
                displayname = name + "/"
                linkname = name + "/"
            if os.path.islink(fullname):
                displayname = name + "@"
                # Note: a link to a directory displays with @ and links with /
            r.append('<li><a href="%s">%s</a></li>'
                    % (urllib.parse.quote(linkname,
                                          errors='surrogatepass'),
                       html.escape(displayname, quote=False)))
        r.append('</ul>\n<hr>\n</body>\n</html>\n')
        encoded = '\n'.join(r).encode(enc, 'surrogateescape')
        f = io.BytesIO()
        f.write(encoded)
        f.seek(0)
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-type", "text/html; charset=%s" % enc)
        self.send_header("Content-Length", str(len(encoded)))
        self.try_send_bug_server_header()
        self.end_headers()
        return f

    def send_head(self):
        """Common code for GET and HEAD commands.

        This sends the response code and MIME headers.

        Return value is either a file object (which has to be copied
        to the outputfile by the caller unless the command was HEAD,
        and must be closed by the caller under all circumstances), or
        None, in which case the caller has nothing further to do.

        """
        path = self.translate_path(self.path)
        f = None
        if os.path.isdir(path):
            parts = urllib.parse.urlsplit(self.path)
            if not parts.path.endswith('/'):
                # redirect browser - doing basically what apache does
                self.send_response(HTTPStatus.MOVED_PERMANENTLY)
                new_parts = (parts[0], parts[1], parts[2] + '/',
                             parts[3], parts[4])
                new_url = urllib.parse.urlunsplit(new_parts)
                self.send_header("Location", new_url)
                self.send_header("Content-Length", "0")
                self.try_send_bug_server_header()
                self.end_headers()
                return None
            for index in self.index_pages:
                index = os.path.join(path, index)
                if os.path.isfile(index):
                    path = index
                    break
            else:
                return self.list_directory(path)

        ctype = self.guess_type(path)
        # check for trailing "/" which should return 404. See Issue17324
        # The test for this was added in test_httpserver.py
        # However, some OS platforms accept a trailingSlash as a filename
        # See discussion on python-dev and Issue34711 regarding
        # parsing and rejection of filenames with a trailing slash
        if path.endswith("/"):
            self.send_error(HTTPStatus.NOT_FOUND, "File not found")
            return None
        try:
            f = open(path, 'rb')
        except OSError:
            self.send_error(HTTPStatus.NOT_FOUND, "File not found")
            return None

        try:
            fs = os.fstat(f.fileno())
            # Use browser cache if possible
            if ("If-Modified-Since" in self.headers
                    and "If-None-Match" not in self.headers):
                # compare If-Modified-Since and time of last file modification
                try:
                    ims = email.utils.parsedate_to_datetime(
                        self.headers["If-Modified-Since"])
                except (TypeError, IndexError, OverflowError, ValueError):
                    # ignore ill-formed values
                    pass
                else:
                    if ims.tzinfo is None:
                        # obsolete format with no timezone, cf.
                        # https://tools.ietf.org/html/rfc7231#section-7.1.1.1
                        ims = ims.replace(tzinfo=datetime.timezone.utc)
                    if ims.tzinfo is datetime.timezone.utc:
                        # compare to UTC datetime of last modification
                        last_modif = datetime.datetime.fromtimestamp(
                            fs.st_mtime, datetime.timezone.utc)
                        # remove microseconds, like in If-Modified-Since
                        last_modif = last_modif.replace(microsecond=0)

                        if last_modif <= ims:
                            self.send_response(HTTPStatus.NOT_MODIFIED)
                            self.try_send_bug_server_header()
                            self.end_headers()
                            f.close()
                            return None

            self.send_response(HTTPStatus.OK)
            self.send_header("Content-type", ctype)
            self.send_header("Content-Length", str(fs[6]))
            self.send_header("Last-Modified",
                self.date_time_string(fs.st_mtime))
            if self._no_sniff_header:
                self.send_header("X-Content-Type-Options", "nosniff")
            self.try_send_bug_server_header()
            self.end_headers()
            return f
        except:
            f.close()
            raise

    def try_send_bug_server_header(self):
        """Try to send the bug server header."""
        if self._bug_server is not None:
            self.send_header("AM-BUG-SERVER-TYPE", self._bug_server.server_type)
        return

    def translate_path(self, path):
        """Translate a /-separated PATH to the local filename syntax.

        Components that mean special things to the local file system
        (e.g. drive or directory names) are ignored.  (XXX They should
        probably be diagnosed.)

        """
        # abandon query parameters
        path = path.split('?',1)[0]
        path = path.split('#',1)[0]
        # Don't forget explicit trailing slash when normalizing. Issue17324
        trailing_slash = path.rstrip().endswith('/')
        try:
            path = urllib.parse.unquote(path, errors='surrogatepass')
        except UnicodeDecodeError:
            path = urllib.parse.unquote(path)
        path = posixpath.normpath(path)
        words = path.split('/')
        words = filter(None, words)
        path = self.directory
        for word in words:
            if os.path.dirname(word) or word in (os.curdir, os.pardir):
                # Ignore components that are not a simple file/directory name
                continue
            path = os.path.join(path, word)
        if trailing_slash:
            path += '/'

        realpath = os.path.realpath(path)
        return realpath

    def guess_type(self, path):

        rtnval = ""

        _, fext = os.path.splitext(path)

        if (fext == ".yaml") or (fext == ".yml"):
            self._no_sniff_header = True
            rtnval = "text/yaml"
        elif (fext == ".log") or (fext == ".jsos") or (fext == ".txt"):
            self._no_sniff_header = True
            rtnval = "text/plain"
        else:
            rtnval = super().guess_type(path)
        
        return rtnval

class TestResultServer(ThreadingHTTPServer):
    """
        Simple HTTP server for browsing and interacting with test results.
    """

    def __init__(self, root_directory: str, server_endpoint: Tuple[str, int], handler_class: Type[SimpleHTTPRequestHandler], bug_server: Optional[BugServerInterface]=None,):
        super().__init__(server_endpoint, handler_class)
        self._root_directory = root_directory
        self._bug_server = bug_server
        return

    def server_bind(self):
        # suppress exception when protocol is IPv4
        with contextlib.suppress(Exception):
            self.socket.setsockopt(
                socket.IPPROTO_IPV6, socket.IPV6_V6ONLY, 0)
        return super().server_bind()

    def finish_request(self, request, client_address):
        self.RequestHandlerClass(request, client_address, self, directory=self._root_directory, bug_server=self._bug_server)
        return


if __name__ == '__main__':
    import argparse
    import contextlib

    parser = argparse.ArgumentParser()

    parser.add_argument('-d', '--directory', default=os.getcwd(), help='serve this directory (default: current directory)')

    parser.add_argument('-b', '--bind', metavar='ADDRESS', default="", help='bind to this address (default: all interfaces)')
    
    parser.add_argument('port', default=8880, type=int, nargs='?', help='bind to this port (default: %(default)s)')
    
    args = parser.parse_args()
    
    svc_endpoint = (args.bind, args.port)
    svc_directory = os.path.abspath(os.path.expandvars(os.path.expanduser(args.directory)))

    bug_svc = try_create_bug_server_interface_from_environment()

    server = TestResultServer(svc_directory, svc_endpoint, TestResultRequestHandler, bug_svc)

    server.serve_forever()
