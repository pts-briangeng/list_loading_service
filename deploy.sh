#!/bin/bash

set -e
cd /content/

usage_and_exit(){
cat << EOF
Usage: deploy.sh [OPTIONS...] --environment=ENVIRONMENT

    -h, --help                                      Print this help message
    -m, --migrate                                   Run Migration after deployment. Default: not set
    --enable-nscd                                   Enable NSCD to permit application containers to user host's name service cache
    --disable-nscd                                  Disable NSCD for name service caching through the host
    -t, --run-tests                                 Run Sanity Tests after deployment. Default: not set
    -u, --user=<username>                           User to run the deployment as. Default: buildmgr
    -e, --environment=<ft|staging|production>       Environment to deploy to. REQUIRED. Default: not set
    -f, --fab-directory=<fab tasks directory>       Directory where the fab tasks are located. Default: /content/fabfile
    -i, --key=<key location>                        User's RSA Key Location. Default: not set

EOF
exit
}

OPTS=$(getopt --options hmtu:e:f:i: --longoptions help,migrate,enable-nscd,disable-nscd,run-tests,user:,environment:,fab-directory:,key: -- "$@")
if [ $? != 0 ]
then
    exit 1
fi

eval set -- "$OPTS"

migrate_param=""
nscd_param=""
key_param=""
run_tests=false
user="buildmgr"
fab_directory="/content/fabfile"
deployment_environment=""

while true ; do
    case "$1" in
        -h|--help)
            usage_and_exit
            ;;
        -m|--migrate)
            migrate_param=",run_migrate=1"
            shift;;
        --enable-nscd)
            nscd_param=",enable_nscd=1"
            shift;;
        --disable-nscd)
            nscd_param=",enable_nscd="
            shift;;
        -t|--run-tests)
            run_tests=true
            shift;;
        -u|--user)
            user=$2;
            shift 2;;
        -e|--environment)
            deployment_environment=$2;
            shift 2;;
        -f|--fab-directory)
            fab_directory=$2;
            shift 2;;
        -i|--key)
            key_param="-i $2"
            shift 2;;
        --) shift; break;;
    esac
done

if [ -z "${deployment_environment}" ]; then
    usage_and_exit
fi

echo "Running Deployment..."
fab --user=$user $key_param --fabfile=$fab_directory full_deploy:$deployment_environment,FQIN,CONFIG_DIR/$deployment_environment$migrate_param$nscd_param

if [ $run_tests == true ]; then
    fab --fabfile=$fab_directory test_integration:$deployment_environment.ini,,'--attr sanity_tests --nocapture',$deployment_environment
fi