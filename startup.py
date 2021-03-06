""" Startup script for the server."""
import argparse
import sys
import tornado.web
import socket
import tornado.options
from metadatastore.mds import MDS, MDSRO
from metadataservice.server.engine import (RunStartHandler, RunStopHandler,
                                           EventDescriptorHandler,
                                           EventHandler, loop)

from metadataservice.server.conf import load_configuration


if __name__ == "__main__":
    config = {}
    parser = argparse.ArgumentParser()
    parser.add_argument('--database', dest='database', type=str,
                        help='name of database to use')
    parser.add_argument('--mongo-host', dest='mongohost', type=str,
                        help='mongodb host to connect to')
    parser.add_argument('--timezone', dest='timezone', type=str,
                        help='Local timezone')
    parser.add_argument('--mongo-port', dest='mongoport', type=int,
                        help='mongodb port to connect')
    parser.add_argument('--service-port', dest='serviceport', type=int,
                        help='port to broadcast from')
    parser.add_argument('--no-auth', dest='auth', action='store_false')
    parser.add_argument('--auth', dest='auth', action='store_true')
    parser.set_defaults(auth=False)
    parser.add_argument('--mongo-user', dest='mongo_user', type=str,
                            help='Mongo username')
    parser.add_argument('--mongo-pwd', dest='mongo_pwd', type=str,
                            help='Mongo password')
    args = parser.parse_args()
    # name of the database server will talk to.
    # If db does not exist, creates one
    if args.database is not None:
        config['database'] = args.database
    else:
        raise KeyError('--database is a required arg')
    # name/ip address of the machine hosting mongodb
    if args.mongohost is not None:
        config['mongohost'] = args.mongohost
    else:
        raise KeyError('--mongo-host is a required arg')
    # US/Eastern for BNL
    if args.timezone is not None:
        config['timezone'] = args.timezone
    else:
        raise KeyError('--timezone is a required arg')
    # port mongo uses on the mongo-host machine, 27017 by default
    if args.mongoport is not None:
        config['mongoport'] = args.mongoport
    else:
        raise KeyError('--mongo-port is a required arg')
    # Port that this server will use to communicate
    if args.serviceport is not None:
        config['serviceport'] = args.serviceport
    else:
        raise KeyError('--service-port is a required arg')
    if args.auth:
        if args.mongo_user and args.mongo_pwd:
            config['mongo_user'] = args.mongo_user
            config['mongo_pwd'] = args.mongo_pwd
        else:
            raise KeyError('--mongo-user and --mongo-pwd required with auth')
    else:
        config['mongo_user'] = None
        config['mongo_pwd'] = None
    libconfig = dict(host=config['mongohost'], port=config['mongoport'],
                     timezone=config['timezone'], database=config['database'],
                     mongo_user= config['mongo_user'], mongo_pwd=config['mongo_pwd'])
    mdsro = MDSRO(version=1, config=libconfig, auth=args.auth)
    mdsrw = MDS(version=1, config=libconfig, auth=args.auth)

    print('Connecting to mongodb...{}:{}/{}'.format(config['mongohost'],
                                                    config['mongoport'],
                                                    config['database']))
    args = sys.argv
    # args.append("--log_file_prefix=/tmp/metadataservice.log")
    # tornado.options.parse_command_line(args)
    application = tornado.web.Application([
        (r'/run_start', RunStartHandler), (r'/run_stop', RunStopHandler),
        (r'/event_descriptor', EventDescriptorHandler),
        (r'/event', EventHandler)
         ], mdsro=mdsro, mdsrw=mdsrw)
    application.listen(config['serviceport'])
    print('Service live on address {}:{}'.format(socket.gethostname(),
                                                 config['serviceport']))
    loop.start()
