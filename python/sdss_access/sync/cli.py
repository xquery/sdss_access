from __future__ import print_function

from os import getenv, makedirs
from os.path import exists, join, basename
from math import log10
from sys import exit
from subprocess import Popen, STDOUT
from shlex import split
from tempfile import TemporaryFile
from time import time, sleep
from glob import iglob
from datetime import datetime

class Cli:
    """Class for providing command line interface (cli) sync scripts, and logs to local disk
    """
    
    tmp_dir = '/tmp'

    def __init__(self, label=None, data_dir=None, verbose=False):
        self.label = label if label else 'sdss_access'
        self.data_dir = data_dir if data_dir else getenv('SDSS_ACCESS_DATA_DIR')
        self.ready = exists(self.data_dir) if self.data_dir else False
        if not self.ready and exists(self.tmp_dir): self.data_dir = self.tmp_dir
        self.now = datetime.now().strftime("%Y%m%d")
        self.env = None
        self.verbose = verbose

    def set_dir(self):
        if exists(self.data_dir) and self.label:
            label_dir = join(self.data_dir,self.label)
            position = len(self.now)+1
            maxnumber = 0
            for dir in iglob(join(label_dir,"{now}_*".format(now=self.now))):
                dirname = basename(dir)
                try: dirnumber = int(dirname[position:])
                except: dirnumber = 0
                maxnumber = max(maxnumber,dirnumber)
            self.dir = join(label_dir,"{now}_{number:03d}".format(now=self.now,number=maxnumber+1))
            if not exists(self.dir):
                if self.verbose: print("SDSS_ACCESS> CREATE {dir}".format(dir=self.dir))
                makedirs(self.dir)
        else: self.dir = None
            
    def get_path(self,index=None):
        try: index = int(index)
        except: index = 0
        return join(self.dir,"{label}_{index:02d}".format(label=self.label,index=index)) if self.dir and self.label else None
    
    def write_lines(self, path=None, lines=None):
        if path and lines:
            with open(path,'w') as file:
                file.write("\n".join(lines)+"\n")

    def get_background_process(self, command=None, logfile=None, errfile=None, pause=1):
        if command:
            stdout = logfile if logfile else STDOUT
            stderr = errfile if errfile else STDOUT
            background_process = Popen(split(str(command)), env=self.env, stdout=stdout, stderr=stderr)
            if pause: sleep(pause)
        else: background_process = None
        return background_process

    def wait_for_processes(self, processes, pause=60):
        print("SDSS_ACCESS> syncing... please wait")
        while any([process.poll() is None for process in processes]): sleep(pause)
        print("SDSS_ACCESS> Done!")
        self.returncode = tuple([process.returncode for process in processes])

    def foreground_run(self, command, test=False, logger=None, logall=False, message=None, outname=None, errname=None):
        """A convenient wrapper to log and perform system calls.

        Parameters
        ----------
        command : str
            The system command to run.  It will be split internally by shlex.split().
        test : bool, optional
            Set this to true to not actually run the commands.
        logger : logging.logging, optional
            If passed a logging object, diagnostic output will be set to this object.
        logall : bool, optional
            Set this to true to always log stdout and stderr (at level DEBUG).
            Otherwise stdout and stderr will only be logged for nonzero status
        message : str, optional
            Call logger.critical(message) with this message and then call
            sys.exit(status).
        outname : str, optional
            If set, use ``outname`` as the name of a file to contain stdout.  It
            is the responsibility of the caller of this function to clean up
            the resulting file.  Otherwise a temporary file will be used.
        errname : str, optional
            Same as ``outname``, but will contain stderr.

        Returns
        -------
        (status,out,err) : tuple
            The exit status, stdout and stderr of the process

        Examples
        --------
        >>> status,out,err = transfer.common.system_call('date')
        """
        if logger is not None:
            logger.debug(command)
        status = 0
        out = ''
        err = ''
        if not test:
            if outname is None:
                outfile = TemporaryFile()
            else:
                outfile = open(outname,'w+')
            if errname is None:
                errfile = TemporaryFile()
            else:
                errfile = open(errname,'w+')
            proc = Popen(split(str(command)),stdout=outfile,stderr=errfile,env=self.env)
            tstart = time()
            while proc.poll() is None:
                elapsed = time() - tstart
                if elapsed > 500000:
                    message = "Process still running after more than 5 days!"
                    proc.kill()
                    break
                tsleep = 10**(int(log10(elapsed))-1)
                if tsleep < 1:
                    tsleep = 1
                sleep(tsleep)
            # proc.wait()
            status = proc.returncode
            outfile.seek(0)
            out = outfile.read()
            errfile.seek(0)
            err = errfile.read()
            outfile.close()
            errfile.close()
            if logger is not None:
                if status == 0 and logall:
                    if len(out) > 0:
                        logger.debug('STDOUT = \n' + out)
                    if len(err) > 0:
                        logger.debug('STDERR = \n' + err)
                if status != 0:
                    logger.error('status = {0}'.format(status))
                    if len(out) > 0:
                        logger.error('STDOUT = \n' + out)
                    if len(err) > 0:
                        logger.error('STDERR = \n' + err)
                    if message is not None:
                        logger.critical(message)
                        exit(status)
        return (status,out,err)

class CliError(Exception):
    pass


