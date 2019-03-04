# tdl-client-test-broker
An ActiveMq broker to be used for testing the clients

## Requirements

- `Python 3.7` (support for `Python 2.x` has been dropped)
- `pip` (ensure it supports `Python 3.7`)

# Setup

```bash
export BROKER_LOCATION=./broker/
export BROKER_VERSION=master

# Checkout
git submodule add git@github.com:julianghionoiu/tdl-client-test-broker.git $BROKER_LOCATION
git submodule update --init

# Switch to tag
pushd . 
cd $BROKER_LOCATION
git checkout $BROKER_VERSION
popd

# Commit
git commit $BROKER_LOCATION -m "Added broker submodule"
```

# Configure

Your configure the version of the ActiveMq broker you need by editing the `activemq-wrapper.properties` file.
The distribution will be downloaded and cached locally.

If you need to further customise the distribution you can edit the files located in `./conf/`.


# Usage

The most common commands are:
```bash
./activemq-wrapper start
./activemq-wrapper status
./activemq-wrapper stop
```
