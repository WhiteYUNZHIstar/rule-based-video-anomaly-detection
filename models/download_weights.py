import sys
import requests

def download(url, out_path):
    r = requests.get(url, stream=True)
    r.raise_for_status()
    with open(out_path, 'wb') as f:
        for chunk in r.iter_content(1024 * 1024):
            if chunk:
                f.write(chunk)

if __name__ == '__main__':
    if len(sys.argv) < 3:
        print('Usage: python download_weights.py <URL> <OUT_PATH>')
        sys.exit(1)
    url = sys.argv[1]
    out = sys.argv[2]
    download(url, out)
    print('Downloaded', out)
