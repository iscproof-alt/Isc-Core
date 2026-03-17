use std::env;
use std::fs;
use std::time::{SystemTime, UNIX_EPOCH};
use sha2::{Sha256, Digest};
use ed25519_dalek::{SigningKey, Signer};
use rand::rngs::OsRng;
use serde_json::json;
extern crate reqwest;

fn sha256_hex(data: &[u8]) -> String {
    let mut h = Sha256::new();
    h.update(data);
    hex::encode(h.finalize())
}

fn canonical_json(v: &serde_json::Value) -> String {
    match v {
        serde_json::Value::Object(map) => {
            let mut keys: Vec<&String> = map.keys().collect();
            keys.sort();
            let pairs: Vec<String> = keys.iter()
                .map(|k| format!("\"{}\":{}", k, canonical_json(&map[*k])))
                .collect();
            format!("{{{}}}", pairs.join(","))
        }
        serde_json::Value::Array(arr) => {
            let items: Vec<String> = arr.iter().map(canonical_json).collect();
            format!("[{}]", items.join(","))
        }
        _ => v.to_string()
    }
}


fn get_rfc3161_timestamp(data: &[u8], tsa_url: &str) -> Result<Vec<u8>, String> {
    use sha2::{Sha256, Digest};
    
    // Build timestamp query (minimal DER encoding)
    let mut hasher = Sha256::new();
    hasher.update(data);
    let hash = hasher.finalize();
    
    // Minimal RFC 3161 timestamp request
    // OID 1.2.840.113549.2.11 = SHA-256
    let mut query = vec![
        0x30, 0x27, // SEQUENCE
        0x02, 0x01, 0x01, // version = 1
        0x30, 0x1f, // MessageImprint SEQUENCE
        0x30, 0x0d, // AlgorithmIdentifier
        0x06, 0x09, // OID
        0x60, 0x86, 0x48, 0x01, 0x65, 0x03, 0x04, 0x02, 0x01, // SHA-256 OID
        0x05, 0x00, // NULL
        0x04, 0x20, // OCTET STRING, 32 bytes
    ];
    query.extend_from_slice(&hash);
    
    let client = reqwest::blocking::Client::new();
    let resp = client
        .post(tsa_url)
        .header("Content-Type", "application/timestamp-query")
        .body(query)
        .timeout(std::time::Duration::from_secs(10))
        .send()
        .map_err(|e| format!("TSA request failed: {}", e))?;
    
    if !resp.status().is_success() {
        return Err(format!("TSA returned status: {}", resp.status()));
    }
    
    Ok(resp.bytes().map_err(|e| e.to_string())?.to_vec())
}

fn main() {
    let args: Vec<String> = env::args().collect();

    if args.len() >= 3 && args[1] == "--keygen" {
        let keyfile = &args[2];
        let signing_key = SigningKey::generate(&mut OsRng);
        let secret_bytes = signing_key.to_bytes();
        let public_bytes = signing_key.verifying_key().to_bytes();
        let fingerprint = &sha256_hex(&public_bytes)[..16];
        let key_data = json!({
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
        eprintln!("Usage: isc_pack_v4 <artifact> <repo> <commit> [--key <keyfile>]");
        eprintln!("       isc_pack_v4 --keygen <keyfile>");
        std::process::exit(2);
    }

    let artifact_path = &args[1];
    let repo = &args[2];
    let commit = &args[3];

    let tsa_url = if let Some(pos) = args.iter().position(|a| a == "--timestamp") {
        Some(args.get(pos + 1).cloned().unwrap_or_else(|| "https://freetsa.org/tsr".to_string()))
    } else {
        None
    };

    let signing_key = if let Some(pos) = args.iter().position(|a| a == "--key") {
        let keyfile = &args[pos + 1];
        let key_data: serde_json::Value = serde_json::from_str(
            &fs::read_to_string(keyfile).expect("cannot read key file")
        ).unwrap();
        let priv_hex = key_data["private"].as_str().unwrap();
        let priv_bytes = hex::decode(priv_hex).unwrap();
        let arr: [u8; 32] = priv_bytes.try_into().unwrap();
        SigningKey::from_bytes(&arr)
    } else {
        SigningKey::generate(&mut OsRng)
    };

    let public_bytes = signing_key.verifying_key().to_bytes();
    let fingerprint = &sha256_hex(&public_bytes)[..16];

    let artifact_bytes = fs::read(artifact_path).expect("cannot read artifact");
    let artifact_hash = sha256_hex(&artifact_bytes);
    let artifact_name = std::path::Path::new(artifact_path)
        .file_name().unwrap().to_str().unwrap().to_string();

    let now = SystemTime::now().duration_since(UNIX_EPOCH).unwrap().as_secs();
    let sealed_at = chrono::DateTime::from_timestamp(now as i64, 0)
        .unwrap().format("%Y-%m-%dT%H:%M:%SZ").to_string();

    let artifact_payload = json!({"name": artifact_name, "sha256": artifact_hash});
    let attestation_payload = json!({"commit": commit, "repo": repo});
    let metadata_payload = json!({
        "arch": std::env::consts::ARCH,
        "os": std::env::consts::OS,
        "sealed_at": sealed_at,
        "tool": "isc_pack_v4",
        "tool_version": "0.1.0"
    });

    let lh01 = sha256_hex(canonical_json(&artifact_payload).as_bytes());
    let lh02 = sha256_hex(canonical_json(&attestation_payload).as_bytes());
    let lh03 = sha256_hex(canonical_json(&metadata_payload).as_bytes());

    // RFC 3161 timestamp (optional)
    let timestamp_payload_hex: Option<String> = if let Some(ref url) = tsa_url {
        match get_rfc3161_timestamp(hex::decode(&lh03).unwrap_or_default().as_slice(), url) {
            Ok(tsr) => {
                println!("Timestamp: obtained from {}", url);
                Some(hex::encode(&tsr))
            }
            Err(e) => {
                eprintln!("Warning: timestamp failed: {}", e);
                None
            }
        }
    } else {
        None
    };
    let lh05 = timestamp_payload_hex.as_ref().map(|h| sha256_hex(h.as_bytes()));

    let mut leaves: Vec<(u64, String)> = vec![
        (1, lh01.clone()),
        (2, lh02.clone()),
        (3, lh03.clone()),
    ];
    if let Some(ref lh) = lh05 {
        leaves.push((5, lh.clone()));
    }
    leaves.sort_by(|a, b| {
        a.0.cmp(&b.0).then(
            hex::decode(&a.1).unwrap().cmp(&hex::decode(&b.1).unwrap())
        )
    });

    let root_input = format!("[{}]",
        leaves.iter().map(|(t,lh)| format!("[{},\"{}\"]", t, lh)).collect::<Vec<_>>().join(",")
    );
    let root = sha256_hex(root_input.as_bytes());
    let sig = signing_key.sign(hex::decode(&root).unwrap().as_slice());

    let pack = json!({
        "version": 4,
        "hash_alg": "sha256",
        "root": root,
        "leaves": leaves.iter().map(|(t,lh)| json!([t, lh])).collect::<Vec<_>>(),
        "payloads": {
            lh01: hex::encode(canonical_json(&artifact_payload).as_bytes()),
            lh02: hex::encode(canonical_json(&attestation_payload).as_bytes()),
            lh03: hex::encode(canonical_json(&metadata_payload).as_bytes()),
        },
        "signatures": [{"alg": "ed25519", "public_key": hex::encode(public_bytes), "signature": hex::encode(sig.to_bytes())}],
        "timestamp_leaf": lh05.as_deref().unwrap_or("none")
    });

    let pack_name = format!("{}_v4_pack.json", artifact_name);
    fs::write(&pack_name, serde_json::to_string_pretty(&pack).unwrap()).unwrap();

    println!("ISCProof Evidence Pack V4");
    println!("artifact:    {}", artifact_name);
    println!("sha256:      {}", artifact_hash);
    println!("sealed_at:   {}", sealed_at);
    println!("root:        {}", root);
    println!("fingerprint: {}", fingerprint);
    println!("");
    println!("PACK CREATED: {}", pack_name);
}
