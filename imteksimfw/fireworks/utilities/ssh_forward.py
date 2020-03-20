#!/usr/bin/env python
"""
Establishes an ssh forward via jump host through (free) local port
"""

import logging

def forward(
  remote_host = "ufr2.isi1.public.ads.uni-freiburg.de",
  remote_port = 445,
  local_port  = None,
  ssh_host    = "132.230.102.164",
  ssh_user    = "sshclient",
  ssh_keyfile = "~/.ssh/sshclient-frrzvm",
  ssh_port    = 22,
  port_file   = '.port' ):
    """Python equivalent of 'ssh -L'.

    Example:
        With default options equivalent to

        ssh  -i ~/.ssh/sshclient-frrzvm -N -L \
          ${RANDOM_FREE_PORT}:ufr2.isi1.public.ads.uni-freiburg.de:445 \
          sshclient@132.230.102.164

        printing the chosen ${RANDOM_FREE_PORT} to screen, if no specific
        port passed via argument "local_port". You can check the connection with
        an smbclient call

        smbclient //localhost/pastewka -p ${RANDOM_FREE_PORT} \
          -A ~/.smbcredential.rz_storage -W PUBLIC

        after port forwarding has been established.

    Args:
        remote_host (str, optional):  Defaults to
            ufr2.isi1.public.ads.uni-freiburg.de (Uni Freiburg RZ storage)
        remote_port (int, optional):  Defaults to '445' (smb)
        local_port  (int, optional):  Defaults to 'None', resulting the
            selection of a random, free port locally.
        ssh_host (str, optional):     Defaults to Uni Freiburg virtual
            machine '132.230.102.164' (jlh)
        ssh_user (str, optional):     Defaults to 'sshclient'
        ssh_keyfile(str, optional):   Defaults to '~/.ssh/sshclient-frrzvm'.
            User home directory '~' is expanded, other shell abbreviations
            are not.
        ssh_port (int, optional):     Defaults to 22 (ssh)
        port_file (str, optional):    Defaults to '.port'. The local port
            is written to this file. Not written if 'None'.

    Returns:
        Nothing.
    """
    logger = logging.getLogger(__name__)

    from os.path import expanduser
    import paramiko, socket, sys
    from imteksimfw.fireworks.utilities.paramiko_forward import forward_tunnel

    # allocate free local port if none specified
    # inspired by
    #   https://www.scivision.dev/python-get-free-network-port
    # and
    #   http://code.activestate.com/recipes/531822-pick-unused-port
    if local_port is None:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.bind(('localhost', 0))
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        addr, local_port = s.getsockname()
        logger.info("Allocated free local port: {:d}".format(local_port))

    # write port number to file for communication with other processes
    if isinstance(port_file,str):
        with open(port_file, mode='w') as f:
            f.write(str(local_port))

    transport = paramiko.Transport((ssh_host, ssh_port))
    pkey = paramiko.RSAKey.from_private_key_file( expanduser( ssh_keyfile ) )

    transport.connect(hostkey=None,
                      username = ssh_user,
                      password = None,
                      pkey     = pkey)

    try:
        forward_tunnel(local_port, remote_host, remote_port, transport)
    except KeyboardInterrupt:
        logger.warn('Port forwarding stopped.')

    try:
      s.close() # fails if s does not exist
    except Exception:
      pass

    return
