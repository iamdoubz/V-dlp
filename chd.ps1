# Main script
$scriptDir = $PSScriptRoot
$arguments = $args
clear

if ([string]::IsNullOrEmpty($arguments)) {
  Write-Host "You didn't tell me what to convert!"
  Read-Host "Press Enter to exit"
  exit
}

if ($arguments -eq "all") {
  Write-Host "Decompressing zips..."
  & "7za.exe" x "*.7z" -mmt=6 -mmemuse=8G -aos -bsp1 -y *>$null
#  *>$null
  Write-Host "Deleting zips..."
  Remove-Item *.7z -Force -ErrorAction SilentlyContinue
  
  Write-Host "Converting..."
  Write-Host "#####################################################"
  Write-Host ""
  
  $totalSaved = 0
  $totalSavedMB = 0
  
  # Process all .cue, .gdi, .iso files recursively
  Get-ChildItem -Path ./ -Recurse -Include *.cue, *.gdi, *.iso | ForEach-Object {
    $ext = "$($_.Extension)"
	if ($ext -eq '.cue'){
	  $tempsize = 0
	  Get-ChildItem -Path "$($_.DirectoryName)" -Recurse -Include *.bin | ForEach-Object {
		$tempsize = $tempsize + (Get-Item $_.FullName).Length
	  }
	  $originalSize = $tempsize + (Get-Item $_.FullName).Length
	} else {
      $originalSize = (Get-Item $_.FullName).Length
    }
	$originalSizeKB = [math]::Round($originalSize / 1024, 2)
    Write-Host "$($_.BaseName)"
    # Get number of processors
	$numproc = $env:NUMBER_OF_PROCESSORS
	if ($numproc -ge 4) {
		$numproc = $numproc - 2
	}
    # Create .chd file
    $chdFile = "$($_.BaseName).chd"
	if (-Not (Test-Path -Path $chdFile)) {
      & "chdman.exe" createcd -np $numproc -i $_.FullName -o $chdFile *>$null
	}
    
    # Get new file size
    $newSize = (Get-Item $chdFile).Length
    $newSizeKB = [math]::Round($newSize / 1024, 2)
    
    # Calculate space saved
    $savedKB = $originalSizeKB - $newSizeKB
	$savedMB = [math]::Round(($originalSize - $newSize) / 1024 / 1024, 2)
    $savedPercent = [math]::Round((($savedKB / $originalSizeKB) * 100), 1)
    
    Write-Host "$savedPercent% space saved ($savedMB MB)"
    Write-Host ""
    
    # Accumulate totals
    $totalSaved += $savedKB
    $totalSavedMB += [math]::Round($savedKB / 1024, 2)
	$totalSavedGB += [math]::Round($savedKB / 1024 / 1024, 2)
  }
  Write-Host "#####################################################"
  Write-Host ""
  Write-Host "Total space saved: $totalSavedGB GB"
  Write-Host ""
  Write-Host "#####################################################"
} else {
  Write-Host "Converting..."
  & "chdman.exe" createcd -i "$arguments" -o "$arguments.chd"
}

Read-Host "Press Enter to exit..."