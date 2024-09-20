import nltk
import time
from processors.sia_an import CybersecuritySentimentAnalyzer
from rich import print
from rich.console import Console
from rich.table import Table
from rich.progress import track

from utils.logging import *

nltk.download('vader_lexicon')

tests = [
    "The vulnerability in the firewall allowed a hacker to breach the system.",
    "Applying a patch improved the system's.",
    "Malware was detected but the antivirus swiftly removed it.",
    "The company's encryption techniques ensured data safety.",
    "A zero-day exploit was used to compromise the server we are putting it for sale",
    "After implementing multi-factor authentication, the system is way more secure",
    "The phishing attack failed due to user awareness training.",
    "The ransomware encrypted all files lmao\ndemanding a hefty ransom rn",
]

analyzer = CybersecuritySentimentAnalyzer()

start_time = time.time()

console = Console()

table = Table(title="Sentiment Analysis", show_header=True, header_style="bold cyan")

table.add_column("Detected", justify="center", style="bold cyan")
table.add_column("Message", justify="left", style="magenta")
table.add_column("Score Type", justify="center", style="bold green")
table.add_column("Value", justify="center", style="yellow")

for i, test in enumerate(track(tests, description="Processing Sentiment Tests...")):
    print_info((i, test))
    scores = analyzer.polarity_scores(test)
    is_illegal = scores['neg'] > 0.5
    row_color = "red" if is_illegal else "green"
    
    table.add_row(
        str(is_illegal),
        test,
        "Negative",
        f"{scores['neg']:.2f}",
        style=row_color
    )
    table.add_row("", "", "Neutral", f"{scores['neu']:.2f}")
    table.add_row("", "", "Positive", f"{scores['pos']:.2f}")
    table.add_row("", "", "Compound", f"{scores['compound']:.2f}")
    table.add_row("", "", "", "")

end_time = time.time()

console.print(table)

console.print(f"\n[bold green]Finished processing {len(tests)} tests in {round(end_time - start_time, 2)} seconds[/bold green]\n")
