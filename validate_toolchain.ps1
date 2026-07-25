$ErrorActionPreference = "Continue"
$passCount = 0
$failCount = 0

function Test-Check {
    param([string]$Name, [scriptblock]$Test)
    Write-Host -NoNewline "Validating $Name... "
    try {
        $result = & $Test
        if ($result -or $result -eq $null) { # Assuming success if no strict boolean false returned but no exception thrown
            Write-Host "PASS" -ForegroundColor Green
            $script:passCount++
        } else {
            Write-Host "FAIL" -ForegroundColor Red
            $script:failCount++
        }
    } catch {
        Write-Host "FAIL ($($_.Exception.Message))" -ForegroundColor Red
        $script:failCount++
    }
}

Write-Host "========================================"
Write-Host " PHASE 1.5: TOOLCHAIN VALIDATION REPORT "
Write-Host "========================================"

Test-Check "Python Version (3.11+)" {
    $ver = python --version 2>&1
    return $ver -match "Python 3\.1[1-9]"
}

Test-Check "Node Version (22 LTS)" {
    $ver = node --version 2>&1
    return $ver -match "v22\."
}

Test-Check "Docker Availability" {
    $ver = docker --version 2>&1
    return $ver -match "Docker version"
}

Test-Check "Git Availability" {
    $ver = git --version 2>&1
    return $ver -match "git version"
}

Test-Check "Environment Template (.env.example)" {
    return (Test-Path ".env.example")
}

Write-Host "----------------------------------------"
if ($failCount -gt 0) {
    Write-Host "STATUS: FAILED ($failCount errors)" -ForegroundColor Red
    exit 1
} else {
    Write-Host "STATUS: PASSED ($passCount checks successful)" -ForegroundColor Green
    exit 0
}
