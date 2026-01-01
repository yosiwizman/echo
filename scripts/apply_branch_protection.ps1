<#
.SYNOPSIS
    Apply branch protection rules to main branch.
.DESCRIPTION
    Requires GITHUB_TOKEN env var with admin access to the repo.
.EXAMPLE
    $env:GITHUB_TOKEN = "ghp_xxx"; .\scripts\apply_branch_protection.ps1
#>

$ErrorActionPreference = "Stop"

$owner = "yosiwizman"
$repo = "echo"
$branch = "main"

if (-not $env:GITHUB_TOKEN) {
    Write-Error "GITHUB_TOKEN environment variable is required with admin access"
    exit 1
}

$headers = @{
    "Accept" = "application/vnd.github+json"
    "Authorization" = "Bearer $($env:GITHUB_TOKEN)"
    "X-GitHub-Api-Version" = "2022-11-28"
}

# Required status check contexts (exact names from CI)
$requiredChecks = @(
    "Brain API Contract Validation",
    "Backend (lint + unit/smoke tests)",
    "Mobile (analyze + tests)",
    "Scaffold Tests (Legacy)"
)

$body = @{
    required_status_checks = @{
        strict = $true
        contexts = $requiredChecks
    }
    enforce_admins = $true
    required_pull_request_reviews = @{
        dismiss_stale_reviews = $true
        require_code_owner_reviews = $true
        required_approving_review_count = 1
    }
    restrictions = $null
    required_linear_history = $true
    allow_force_pushes = $false
    allow_deletions = $false
    required_conversation_resolution = $true
} | ConvertTo-Json -Depth 10

Write-Host "Applying branch protection to $owner/$repo:$branch..."
Write-Host "Required checks: $($requiredChecks -join ', ')"

try {
    $uri = "https://api.github.com/repos/$owner/$repo/branches/$branch/protection"
    $response = Invoke-RestMethod -Uri $uri -Method Put -Headers $headers -Body $body -ContentType "application/json"
    Write-Host "`n✓ Branch protection applied successfully!"
    
    # Verify by fetching back
    Write-Host "`nVerifying protection settings..."
    $verify = Invoke-RestMethod -Uri $uri -Method Get -Headers $headers
    Write-Host "`nProtection settings:"
    Write-Host "  - Required checks: $($verify.required_status_checks.contexts -join ', ')"
    Write-Host "  - Strict status checks: $($verify.required_status_checks.strict)"
    Write-Host "  - Enforce admins: $($verify.enforce_admins.enabled)"
    Write-Host "  - Required approvals: $($verify.required_pull_request_reviews.required_approving_review_count)"
    Write-Host "  - Dismiss stale reviews: $($verify.required_pull_request_reviews.dismiss_stale_reviews)"
    Write-Host "  - Require code owner reviews: $($verify.required_pull_request_reviews.require_code_owner_reviews)"
    Write-Host "  - Linear history: $($verify.required_linear_history.enabled)"
    Write-Host "  - Allow force pushes: $($verify.allow_force_pushes.enabled)"
    Write-Host "  - Allow deletions: $($verify.allow_deletions.enabled)"
    
} catch {
    Write-Error "Failed to apply branch protection: $($_.Exception.Message)"
    if ($_.Exception.Response) {
        $reader = [System.IO.StreamReader]::new($_.Exception.Response.GetResponseStream())
        Write-Host "Response: $($reader.ReadToEnd())"
    }
    exit 1
}
