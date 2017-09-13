param (
    [string]$Command = "start"
)

$ScriptFolder = (Get-Item -Path ".\" -Verbose).FullName

$CacheFolder = "$($ScriptFolder)/.cache"
$ConfFolder = "$($ScriptFolder)/conf"

if (-Not (Test-Path $CacheFolder))
{
	New-Item -ItemType directory -Path $CacheFolder
}

# Load properties from properties file
$ActiveMqProps = ConvertFrom-StringData (Get-Content .\activemq-wrapper.properties -raw)
Write-Host "Requiring ActiveMq version:" $ActiveMqProps.BROKER_VERSION

$ActiveMqHome = "$($CacheFolder)/apache-activemq-$($ActiveMqProps.BROKER_VERSION)"
$ActiveMqBin = "$($ActiveMqHome)/bin/activemq.bat"

# Ensure that the required version is stored in local cache
if (-Not (Test-Path $ActiveMqBin))
{
	$DownloadedArtifact = "$($CacheFolder)/last_download.zip"
    Write-Host "Artifact: $($DownloadedArtifact)"

    Write-Host "Version not found in local cache. Downloading from: $($ActiveMqProps.DESTINATION_URL_WIN)"

    $WebClient = New-Object System.Net.WebClient
	$WebClient.DownloadFile($ActiveMqProps.DESTINATION_URL_WIN, $DownloadedArtifact)

	Add-Type -AssemblyName System.IO.Compression.FileSystem

	[System.IO.Compression.ZipFile]::ExtractToDirectory($DownloadedArtifact, $CacheFolder)
}
else
{
	Write-Host "Version found in local cache."
}

# Wrap the activemq broker commands
Write-Host "Execute: $($ActiveMqBin)"

$ConfFile = "$($ConfFolder)/activemq.xml"
$ExtraOpts = "xbean:file:$($ConfFile)"

#if ($Command == "stop") {
#   $ExtraOpts = ""
#}

# Retrieve JMX options. ACTIVEMQ_OPTS is being used by the activemq_bin
#JMX_HOST=`cat ${conf_file} | grep -oe "connectorHost=[^ ]*" | cut -d "\"" -f2`
#JMX_PORT=`cat ${conf_file} | grep -oe "connectorPort=[^ ]*" | cut -d "\"" -f2`
#export ACTIVEMQ_OPTS="-Dactivemq.jmx.url=service:jmx:rmi:///jndi/rmi://${JMX_HOST}:${JMX_PORT}/jmxrmi"

# Run
#$ActiveMqBin "$@" "$($ExtraOpts)"

# Test run
Start-Process $ActiveMqBin $Command
