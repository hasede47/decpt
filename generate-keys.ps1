$keys_dir = "tpot-runtime\data\cowrie\keys"
if (-Not (Test-Path -Path $keys_dir)) {
    New-Item -ItemType Directory -Force -Path $keys_dir
}

Write-Host "Generating fresh Cowrie SSH keys..."

# RSA
ssh-keygen -t rsa -b 2048 -f "$keys_dir\ssh_host_rsa_key" -N "" -q
# DSA
ssh-keygen -t dsa -f "$keys_dir\ssh_host_dsa_key" -N "" -q
# ECDSA
ssh-keygen -t ecdsa -b 256 -f "$keys_dir\ssh_host_ecdsa_key" -N "" -q
# ED25519
ssh-keygen -t ed25519 -f "$keys_dir\ssh_host_ed25519_key" -N "" -q

Write-Host "Keys generated successfully."
