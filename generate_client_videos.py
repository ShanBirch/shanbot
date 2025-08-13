import
sys
import
os
from
pathlib
import
Path

print('Generating videos for clients with available data...')

# Import the process_client_data function
sys.path.append('.')
from simple_blue_video_client_folders import process_client_data

# Client data files we found
clients_data = [
    {'data_file': 'clients/Shannon_Birch/data/Shannon_Birch_2025-03-10_fitness_wrapped_data.json', 'output_file': 'output/Shannon_Birch_fitness_wrapped.mp4'},
    {'data_file': 'clients/Shannon/data/Shannon_Birch_fitness_wrapped_data.json', 'output_file': 'output/Shannon_fitness_wrapped.mp4'},
    {'data_file': 'clients/Ben/data/Ben_Pryke_fitness_wrapped_data.json', 'output_file': 'output/Ben_Pryke_fitness_wrapped.mp4'}
]

# Process each client
for client in clients_data:
    data_file = client['data_file']
    output_file = client['output_file']
    print(f'Processing {data_file}...')
    try:
        # Make sure output directory exists
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        # Check if data file exists
        if not os.path.exists(data_file):
            print(f'Error: Data file {data_file} not found')
            continue
        # Process the client data
        process_client_data(data_file, output_file, None)
        print(f'Successfully generated video for {data_file}')
    except Exception as e:
        print(f'Error processing {data_file}: {e}')

print('Video generation complete!')
