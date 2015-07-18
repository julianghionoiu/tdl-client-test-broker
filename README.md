# tdl-client-test-broker
An ActiveMq broker to be used for testing the clients

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
