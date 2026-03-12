import os
import tweepy


def _get_client() -> tweepy.Client | None:
    api_key = os.getenv("TWITTER_API_KEY")
    api_secret = os.getenv("TWITTER_API_SECRET")
    access_token = os.getenv("TWITTER_ACCESS_TOKEN")
    access_secret = os.getenv("TWITTER_ACCESS_TOKEN_SECRET")

    if not all([api_key, api_secret, access_token, access_secret]):
        return None

    return tweepy.Client(
        consumer_key=api_key,
        consumer_secret=api_secret,
        access_token=access_token,
        access_token_secret=access_secret,
    )


async def surface(text: str):
    client = _get_client()
    if client is None:
        print(f"no surface configured. thought stays internal: {text[:60]}...")
        return

    if len(text) > 280:
        text = text[:277] + "..."

    client.create_tweet(text=text)
