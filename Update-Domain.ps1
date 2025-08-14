# Get the CSV Files
$csvFiles = New-Object System.Collections.ArrayList
$requiredFiles = @("day_0.csv", "day_1.csv", "day_2.csv")
foreach ($file in $requiredFiles) {
    if (-not (Test-Path -Path "$PSScriptRoot\$file")) {
        Write-Host "Required file $file not found in this directory."
        exit
    }
    else {
        $csvFiles.Add((Get-ChildItem -Path "$PSScriptRoot\" -Filter $file)) | Out-Null
    }
}

# set a random domain
$domain = "vandelayindustries"
$domainRandomNumber = Get-Random -Minimum 1000 -Maximum 9999
$domainSuffix = ".com"
$domainName = "$domain$domainRandomNumber$domainSuffix"

foreach ($csv in $csvFiles) {
    # Import the CSV file
    $csvData = Import-Csv -Path $csv.FullName

    # Loop through each row in the CSV
    foreach ($row in $csvData) {
        # Generate a new email address
        $newEmail = "$($row.first_name).$($row.last_name)@$domainName"

        # Update the email address in the CSV data
        $row.email = $newEmail.ToLower()
    }

    # Export the updated CSV data to a new file
    $csvData | Export-Csv -Path $csv.FullName -NoTypeInformation
}

Write-Output "CSV users updated with new domain name: $domainName"