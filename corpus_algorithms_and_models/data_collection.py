import requests
import urllib
from bs4 import BeautifulSoup

class RequestGuard:
    def __init__(self, link):
        """May ingest any link"""
        parsed = urllib.parse.urlparse(link)
        self.domain = parsed.netloc
        self.scheme = parsed.scheme
        self.forbidden = self.parse_robots()

    def parse_robots(self):
        """Returns a list of forbidden paths"""
        robots_text = requests.get(f"{self.scheme}://{self.domain}/robots.txt").text
        forbidden = [f[10:] for f in robots_text.split("\n") if f.startswith("Disallow: ")]
        return forbidden

    def can_follow_link(self, link):
        """Returns true where the passed link is not forbidden"""
        parsed = urllib.parse.urlparse(link)
        if parsed.netloc != self.domain:
            return False
        if any(parsed.path.startswith(f) for f in self.forbidden):
            return False
        return True

    def make_get_request(self, *args, **kwargs):
        """Wraps requests.get to check against robots.txt first"""
        if self.can_follow_link(args[0]):
            return requests.get(*args, **kwargs)


def save_zip_links(url, subreddit_list):
    zip_links = []
    try:
        guard = RequestGuard(url)

        print(f"Visiting main URL: {url}...")
        response = guard.make_get_request(url)
        if response is None:
            print(f"Cannot access {url} as per robots.txt.")
            return

        soup = BeautifulSoup(response.text, 'html.parser')

        for link in soup.find_all('a', href=True)[1:]:
            href = link['href']
            if href.startswith('/'):
                href = url.rstrip('/') + href

            print(f"Visiting link: {href}...")
            try:
                sub_response = guard.make_get_request(f"{url}{href}")
                if sub_response is None:
                    print(f"Cannot access {href} as per robots.txt.")
                    continue

                sub_soup = BeautifulSoup(sub_response.text, 'html.parser')

                for sub_link in sub_soup.find_all('a', href=True)[1:]:
                    sub_href = sub_link['href']
                    if sub_href.endswith('.zip'):
                        full_zip_href = urllib.parse.urljoin(href, sub_href)
                        decoded_zip_href = urllib.parse.unquote(full_zip_href)
                        
                        proper_name = decoded_zip_href[len(href) - 2:decoded_zip_href.rfind('.corpus.zip')] # decoded_zip_href.rfind('.corpus.zip')
                        zip_links.append(proper_name)
                        print(f"Found .zip link: {proper_name}")

            except requests.RequestException as sub_e:
                print(f"Failed to visit {href}: {sub_e}")
    except requests.RequestException as e:
        print(f"Failed to visit {url}: {e}")

    subreddit_list.extend(zip_links)
    print("All .zip links collected:", zip_links)


url = "https://zissou.infosci.cornell.edu/convokit/datasets/subreddit-corpus/corpus-zipped/"
subreddit_list = []
save_zip_links(url, subreddit_list)

if __name__ == "__main__":
    print("Collected .zip links:")
    for zip_link in subreddit_list:
        print(zip_link)