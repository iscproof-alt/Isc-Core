use std::fs;
use std::path::Path;
use std::collections::HashMap;
use sha2::{Sha256, Digest};
use ed25519_dalek::{SigningKey, Signer};
use rand::rngs::OsRng;
use serde::{Deserialize, Serialize};
use chrono::Utc;

#[derive(Serialize, Deserialize)]
struct Manifest {
    pack_version: u32,
    signature_version: u32,
    tool_version: String,
    sealed_at: String,
    os: String,
    arch: String,
    artifact_name: String,
    artifact_sha256: String,
    repo: String,
    commit: String,
    producer_fingerprint: String,
    files: HashMap<String, String>,
}

fn sha256_file(path: &Path) -> String {
    let data = fs::read(path).expect("cannot read file");
    let mut hasher = Sha256::new();
    hasher.update(&data);
    hex::encode(hasher.finalize())
}

fn sha256_bytes(data: &[u8]) -> String {
    let mut hasher = Sha256::new();
    hasher.update(data);
    hex::encode(hasher.finalize())
}

fn main() {
    let args: Vec<String> = std::env::args().collect();

    if args.len() >= 3 && args[1] == "--keygen" {
        let keyfile = &args[2];
        let signing_key = SigningKey::generate(&mut OsRng);
        let secret_bytes = signing_key.to_bytes();
        let public_bytes = signing_key.verifying_key().to_bytes();
        let fingerprint = sha256_bytes(&public_bytes)[..16].to_string();
        
        let key_data = serde_json::json!({
            "private": hex::encode(secret_bytes),
            "public": hex::encode(public_bytes),
            "fingerprint": fingerprint
        });
        
        fs::write(keyfile, serde_json::to_string_pretty(&key_data).unwrap()).unwrap();
        println!("Key generated: {}", keyfile);
        println!("Fingerprint: {}", fingerprint);
        return;
    }

    if args.len() < 4 {
        eprintln!("Usage: isc_pack <artifact> <repo> <commit> [--key <keyfile>]");
        eprintln!("       isc_pack --keygen <keyfile>");
        std::process::exit(1);
    }

    let artifact_path = Path::new(&args[1]);
    let repo = &args[2];
    let commit = &args[3];
    
    let keyfile = if args.len() > 5 && args[4] == "--key" {
        args[5].clone()
    } else {
        "isc_key.json".to_string()
    };
    
    if !Path::new(&keyfile).exists() {
        eprintln!("Key not found: {}. Run: isc_pack --keygen {}", keyfile, keyfile);
        std::process::exit(1);
    }
    
    let key_data: serde_json::Value = serde_json::from_str(
        &fs::read_to_string(&keyfile).unwrap()
    ).unwrap();
    
    let private_hex = key_data["private"].as_str().unwrap();
    let private_bytes = hex::decode(private_hex).unwrap();
    let secret_array: [u8; 32] = private_bytes.try_into().unwrap();
    let signing_key = SigningKey::from_bytes(&secret_array);
    let fingerprint = key_data["fingerprint"].as_str().unwrap().to_string();
    
    let artifact_sha256 = sha256_file(artifact_path);
    let artifact_name = artifact_path.file_name().unwrap().to_str().unwrap().to_string();
    let sealed_at = Utc::now().format("%Y-%m-%dT%H:%M:%SZ").to_string();
    
    let mut files = HashMap::new();
    files.insert(artifact_name.clone(), artifact_sha256.clone());
    
    let manifest = Manifest {
        pack_version: 2,
        signature_version: 1,
        tool_version: "0.1.0".to_string(),
        sealed_at: sealed_at.clone(),
        os: std::env::consts::OS.to_string(),
        arch: std::env::consts::ARCH.to_string(),
        artifact_name: artifact_name.clone(),
        artifact_sha256: artifact_sha256.clone(),
        repo: repo.clone(),
        commit: commit.clone(),
        producer_fingerprint: fingerprint.clone(),
        files,
    };
    
    let manifest_json = serde_json::to_string_pretty(&manifest).unwrap();
    let manifest_hash = sha256_bytes(manifest_json.as_bytes());
    let signature = signing_key.sign(manifest_hash.as_bytes());
    let sig_hex = hex::encode(signature.to_bytes());
    
    let tmp = std::env::temp_dir().join("isc_pack_tmp");
    fs::create_dir_all(&tmp).unwrap();
    fs::write(tmp.join("manifest.json"), &manifest_json).unwrap();
    fs::write(tmp.join("manifest.hash"), &manifest_hash).unwrap();
    fs::write(tmp.join("signature.sig"), &sig_hex).unwrap();
    fs::write(tmp.join("public.key"), key_data["public"].as_str().unwrap()).unwrap();
    
    let pack_name = format!("{}_evidence_pack.tar", 
        artifact_path.file_stem().unwrap().to_str().unwrap());
    let pack_file = fs::File::create(&pack_name).unwrap();
    let mut tar = tar::Builder::new(pack_file);
    tar.append_path_with_name(tmp.join("manifest.json"), "manifest.json").unwrap();
    tar.append_path_with_name(tmp.join("manifest.hash"), "manifest.hash").unwrap();
    tar.append_path_with_name(tmp.join("signature.sig"), "signature.sig").unwrap();
    tar.append_path_with_name(tmp.join("public.key"), "public.key").unwrap();
    tar.append_path_with_name(artifact_path, &artifact_name).unwrap();
    tar.finish().unwrap();
    
    println!("→ artifact_name:    {}", artifact_name);
    println!("→ artifact_sha256:  {}", artifact_sha256);
    println!("→ sealed_at:        {}", sealed_at);
    println!("→ os/arch:          {}/{}", std::env::consts::OS, std::env::consts::ARCH);
    println!("");
    println!("✔ PACK CREATED: {}", pack_name);
    println!("  producer_fingerprint: {}", fingerprint);
    println!("  pack_version: 2 | sig_version: 1 | tool: 0.1.0");
}
