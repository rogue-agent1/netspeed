#!/usr/bin/env python3
"""netspeed - Simple network speed test."""
import urllib.request, time, argparse, sys, json

TEST_URLS = [
    ('Cloudflare 10MB', 'https://speed.cloudflare.com/__down?bytes=10000000'),
    ('Cloudflare 1MB', 'https://speed.cloudflare.com/__down?bytes=1000000'),
    ('Cloudflare 100KB', 'https://speed.cloudflare.com/__down?bytes=100000'),
]

def download_test(url, label=''):
    start = time.time()
    total = 0
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'netspeed/1.0'})
        with urllib.request.urlopen(req, timeout=30) as r:
            while True:
                chunk = r.read(65536)
                if not chunk: break
                total += len(chunk)
    except Exception as e:
        return {'error': str(e), 'label': label}
    
    elapsed = time.time() - start
    speed_mbps = (total * 8) / (elapsed * 1000000) if elapsed > 0 else 0
    
    return {
        'label': label, 'bytes': total, 'seconds': round(elapsed, 2),
        'speed_mbps': round(speed_mbps, 2), 'speed_mbytes': round(total / elapsed / 1048576, 2)
    }

def latency_test(host='1.1.1.1', count=5):
    import subprocess
    try:
        r = subprocess.run(['ping', '-c', str(count), '-q', host], capture_output=True, text=True, timeout=10)
        import re
        m = re.search(r'([\d.]+)/([\d.]+)/([\d.]+)/([\d.]+)', r.stdout)
        if m:
            return {'min': float(m.group(1)), 'avg': float(m.group(2)),
                    'max': float(m.group(3)), 'host': host}
    except: pass
    return {'error': 'ping failed', 'host': host}

def main():
    p = argparse.ArgumentParser(description='Network speed test')
    p.add_argument('--size', choices=['small','medium','large'], default='medium')
    p.add_argument('--latency', action='store_true', help='Also test latency')
    p.add_argument('-j', '--json', action='store_true')
    p.add_argument('-u', '--url', help='Custom download URL')
    args = p.parse_args()

    results = []
    
    if args.latency:
        print("Testing latency...")
        lat = latency_test()
        if 'error' not in lat:
            print(f"  Latency: {lat['avg']:.1f}ms (min {lat['min']:.1f}, max {lat['max']:.1f})")
        results.append({'type': 'latency', **lat})

    if args.url:
        tests = [('Custom', args.url)]
    elif args.size == 'small':
        tests = [TEST_URLS[2]]
    elif args.size == 'large':
        tests = [TEST_URLS[0]]
    else:
        tests = [TEST_URLS[1]]

    print("Testing download speed...")
    for label, url in tests:
        sys.stdout.write(f"  {label}... ")
        sys.stdout.flush()
        result = download_test(url, label)
        if 'error' in result:
            print(f"Error: {result['error']}")
        else:
            print(f"{result['speed_mbps']:.1f} Mbps ({result['speed_mbytes']:.1f} MB/s) in {result['seconds']:.1f}s")
        results.append({'type': 'download', **result})

    if args.json:
        print(json.dumps(results, indent=2))

if __name__ == '__main__':
    main()
