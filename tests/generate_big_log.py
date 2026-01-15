
import random
from datetime import datetime, timedelta

def generate_logs(filename="big_auth.log", count=10000):
    print(f"Generating {count} logs into {filename}...")
    
    start_time = datetime.now() - timedelta(hours=24)
    
    ips = [f"192.168.1.{i}" for i in range(10, 20)]
    attack_ips = ["45.76.123.45", "103.20.1.5", "185.100.1.1"]
    users = ["admin", "root", "user1", "test", "postgres"]
    
    with open(filename, "w") as f:
        for i in range(count):
            current_time = start_time + timedelta(seconds=i * (86400 / count))
            ts = current_time.strftime("%b %d %H:%M:%S")
            host = "webserver"
            
            # 5% chance of attack sequence
            if random.random() < 0.05:
                attack_type = random.choice(["bruteforce", "root", "file", "multi"])
                attacker = random.choice(attack_ips)
                
                if attack_type == "bruteforce":
                    # Generate 5-10 failures
                    user = "admin"
                    for _ in range(random.randint(5, 10)):
                        line = f"{ts} {host} sshd[{random.randint(10000,99999)}]: Failed password for {user} from {attacker} port {random.randint(30000,60000)} ssh2\n"
                        f.write(line)
                        
                elif attack_type == "root":
                    line = f"{ts} {host} sshd[{random.randint(10000,99999)}]: Accepted password for root from {attacker} port {random.randint(30000,60000)} ssh2\n"
                    f.write(line)
                    
                elif attack_type == "file":
                    cmd = random.choice(["vim /etc/passwd", "nano /etc/shadow", "cp /etc/ssh/sshd_config"])
                    line = f"{ts} {host} sudo[{random.randint(10000,99999)}]: {users[0]} : TTY=pts/0 ; PWD=/home/admin ; USER=root ; COMMAND={cmd}\n"
                    f.write(line)

                elif attack_type == "multi":
                     for u in users[:4]:
                        line = f"{ts} {host} sshd[{random.randint(10000,99999)}]: Failed password for invalid user {u} from {attacker} port {random.randint(30000,60000)} ssh2\n"
                        f.write(line)

            else:
                # Normal traffic
                user = random.choice(users)
                ip = random.choice(ips)
                if random.random() < 0.8:
                    msg = f"Accepted publickey for {user} from {ip} port {random.randint(30000,60000)} ssh2"
                else: 
                     msg = f"Disconnecting user {user} {ip} port {random.randint(30000,60000)}: Change of username or service not allowed"
                
                line = f"{ts} {host} sshd[{random.randint(10000,99999)}]: {msg}\n"
                f.write(line)
    
    print("Done!")

if __name__ == "__main__":
    generate_logs("tests/test_logs/big_auth.log")
