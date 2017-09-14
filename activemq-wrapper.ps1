param (
    [string]$Command = "start"
)

$ScriptFolder = (Get-Item -Path ".\" -Verbose).FullName

$CacheFolder = "$($ScriptFolder)/.cache"
$ConfFolder = "$($ScriptFolder)/conf"

if (-Not (Test-Path $CacheFolder)) {
	New-Item -ItemType directory -Path $CacheFolder
}

# Load properties from properties file
$ActiveMqProps = ConvertFrom-StringData (Get-Content .\activemq-wrapper.properties -raw)
Write-Host "Requiring ActiveMq version:" $ActiveMqProps.BROKER_VERSION

$ActiveMqHome = "$($CacheFolder)/apache-activemq-$($ActiveMqProps.BROKER_VERSION)"
$ActiveMqBin = "$($ActiveMqHome)/bin/activemq.bat"

# Ensure that the required version is stored in local cache
if (-Not (Test-Path $ActiveMqBin)) {
	$DownloadedArtifact = "$($CacheFolder)/last_download.zip"
    Write-Host "Artifact: $($DownloadedArtifact)"

    Write-Host "Version not found in local cache. Downloading from: $($ActiveMqProps.DESTINATION_URL)"

    $WebClient = New-Object System.Net.WebClient
	$WebClient.DownloadFile($ActiveMqProps.DESTINATION_URL, $DownloadedArtifact)

	Add-Type -AssemblyName System.IO.Compression.FileSystem

	[System.IO.Compression.ZipFile]::ExtractToDirectory($DownloadedArtifact, $CacheFolder)
}
else {
	Write-Host "Version found in local cache."
}

# Wrap the activemq broker commands
Write-Host "Execute: $($ActiveMqBin)"

$ConfFile = "$($ConfFolder)/activemq.xml"

$ExtraOpts = "xbean:$([System.Uri]"file://$($ConfFile)")"

if ($Command -eq "stop") {
   $ExtraOpts = ""
}

# Retrieve JMX options. ACTIVEMQ_OPTS is being used by the activemq_bin
[xml] $ConfXml = Get-Content $ConfFile
$ManagementContext = $ConfXml.beans.broker.managementContext.managementContext;
$JmxHost = $ManagementContext.connectorHost
$JmxPort = $ManagementContext.connectorPort
$env:ACTIVEMQ_OPTS = "-Dactivemq.jmx.url=service:jmx:rmi:///jndi/rmi://$($JmxHost):$($JmxPort)/jmxrmi"

# Run
Start-Process cmd -ArgumentList "/k $($ActiveMqBin) $($Command) $($ExtraOpts)"

function Wait-Until-Port-Is-Open {
	param (
		[string]$port
	)
	
	$delay = 5
	$n = 0
	
	do {
		Write-Host "Is application listening on port $($port)?"
		$Test = Test-NetConnection -ComputerName localhost -Port $JettyPort
		if ($Test.TcpTestSucceeded) {
			Write-Host "Yes"
			break
		}
		else {
			Write-Host "No. Retrying in $($delay) seconds."
		}
		
		$n = $n + 1
		Start-Sleep -s $delay
	}
	while ($n -lt 5)
}

# Only on start
if ($Command -eq "start") {
	[xml] $JettyXml = Get-Content "$($ConfFolder)/jetty.xml"
	$JettyPort = ($JettyXml.beans.bean.property | ? {$_.name -eq "port"}).value
	Wait-Until-Port-Is-Open($JettyPort)
}
