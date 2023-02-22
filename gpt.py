import argparse
import openai
import os

# Create the argument parser
parser = argparse.ArgumentParser(description='Use OpenAI GPT-3 API to generate text.')
parser.add_argument('prompt', type=str, help='the prompt to generate text from')
parser.add_argument('-m', '--model', type=str, default='text-davinci-003', help='the GPT-3 model to use')
parser.add_argument('-t', '--temperature', type=float, default=0.8, help='the sampling temperature')
parser.add_argument('-max', '--max-tokens', type=int, default=800, help='the maximum number of tokens to generate')

# Parse the arguments
args = parser.parse_args()

# Set the OpenAI API key
openai.api_key = os.getenv("OPENAI_API_KEY")

# Call the OpenAI API
r = openai.Completion.create(model=args.model, prompt=args.prompt, temperature=args.temperature, max_tokens=args.max_tokens)
response = r.choices[0]['text']

# Print the generated text
print('\n' + response.strip("\n") + '\n')
