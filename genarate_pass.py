import secrets
import string

def generate_strong_passphrase(num_words=6):
    wordlist = [
        "quantum", "cipher", "nebula", "rocket", "guitar", "keyboard", 
        "mountain", "ocean", "purple", "dinosaur", "stapler", "battery",
        "velocity", "horizon", "eclipse", "matrix", "firewall", "router",
        "protocol", "packet", "socket", "kernel", "syntax", "binary",
        "obsidian", "vortex", "phantom", "vector", "entropy", "spectrum"
    ]
    
    secure_words = [secrets.choice(wordlist) for _ in range(num_words)]
    passphrase = "-".join(secure_words)
    
    random_number = str(secrets.randbelow(100))
    random_symbol = secrets.choice("!@#$%^&*")
    
    return f"{passphrase}-{random_number}{random_symbol}"

if __name__ == "__main__":
    print("MASTER PASSWORD GENERATOR")
    print("Write this on physical paper. Do not save digitally.\n")
    
    new_master = generate_strong_passphrase()
    print(f"Master Password: {new_master}")