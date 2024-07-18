import discord
import praw
import re

# Reddit API credentials
reddit = praw.Reddit(client_id='',
                     client_secret='',
                     user_agent='my_reddit_bot')

# Discord bot token
TOKEN = ''

# Create an instance of a Client. This is the connection to Discord.
intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)

# Global variables to store fetched posts, posted post IDs, and current index
posts = []
posted_post_ids = set()  # Track IDs of posted posts
current_index = 0

# Function to fetch posts from a subreddit
def fetch_posts(subreddit_name):
    global posts
    subreddit = reddit.subreddit(subreddit_name)
    fetched_posts = [post for post in subreddit.new(limit=1000) if post.id not in posted_post_ids]
    posts = [post for post in fetched_posts if post.url.endswith(('mp4', 'webm', 'gifv')) or 'redgifs.com' in post.url]
    
    print(f"Fetched {len(fetched_posts)} posts from r/{subreddit_name}")  # Debugging output
    if not posts:
        posts = []  # Ensure posts is an empty list if no posts are found
    return posts

# Function to get the next posts
def get_next_posts(num_posts=1):
    global posts, current_index
    results = []
    for _ in range(num_posts):
        if current_index < len(posts):
            post = posts[current_index]
            posted_post_ids.add(post.id)  # Track this post as posted
            current_index += 1
            
            # Extract video URL or handle RedGIFs
            if 'redgifs.com' in post.url:
                # Extract video URL from RedGIFs
                video_url_match = re.search(r'(https://.+?\.mp4)', post.url)
                video_url = video_url_match.group(1) if video_url_match else post.url
            else:
                video_url = post.url
            
            results.append(f"**{post.title}**\n{video_url}")
        else:
            results.append("No more video posts available.")
            break  # Exit the loop if there are no more posts
    return results

@client.event
async def on_ready():
    print(f'We have logged in as {client.user}')

@client.event
async def on_message(message):
    global current_index, posts

    if message.author == client.user:
        return

    if message.content.startswith('!reddit'):
        try:
            parts = message.content.split(' ')
            subreddit_name = parts[1]

            await message.channel.send(f"Fetching video posts from r/{subreddit_name}...")
            fetch_posts(subreddit_name)
            
            if posts:
                current_index = 0
                post = get_next_posts()
                await message.channel.send(post[0])  # First video post
            else:
                await message.channel.send("No video posts found.")
        
        except IndexError:
            await message.channel.send('Please specify a subreddit. Usage: `!reddit <subreddit>`')
        except Exception as e:
            await message.channel.send(f'An error occurred: {e}')

    elif message.content.startswith('!next'):
        try:
            parts = message.content.split(' ')
            num_posts = int(parts[1]) if len(parts) > 1 else 1

            if num_posts < 1:
                await message.channel.send("Please specify a number greater than zero.")
                return
            
            next_posts = get_next_posts(num_posts)
            for post in next_posts:
                await message.channel.send(post)
        
        except ValueError:
            await message.channel.send('Please specify a valid number of posts. Usage: `!next <num_posts>`')
        except IndexError:
            await message.channel.send('Please specify a number of posts. Usage: `!next <num_posts>`')
        except Exception as e:
            await message.channel.send(f'An error occurred: {e}')

client.run(TOKEN)
