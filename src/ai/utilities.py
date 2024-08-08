import os
import cv2
import uuid
import json
import time
import shutil
from flask import render_template

class FileHandler:

  def __init__(self):
    self.upload_folder = 'data/user_data/'

  def remove_erronous_files(self, encoded_email, entity_id):
    video_folder = f'data/user_data/{encoded_email}/data/entities/{entity_id}/videos/'
    all_files = os.listdir(video_folder)
    for file in all_files:
      if not file.endswith('.mp4'):
        self.write_to_log(encoded_email, entity_id, f"Lost file chunk File found. Removing file: {file}")
        os.remove(os.path.join(video_folder, file))

  def write_to_log(self, encoded_email, entity_id, message):
    log_file = f'data/user_data/{encoded_email}/data/entities/{entity_id}/log.txt'
    with open(log_file, 'a') as f:
      f.write(f"{message}\n")

  def empty_log(self, encoded_email, entity_id):
    log_file = f'data/user_data/{encoded_email}/data/entities/{entity_id}/log.txt'
    with open(log_file, 'w') as f:
      f.write("")

  def get_entity_log(self, encoded_email, entity_id):
    log_file = f'data/user_data/{encoded_email}/data/entities/{entity_id}/log.txt'
    log_data = f"{time.strftime('%Y-%m-%d %H:%M:%S')} - Log\n"
    try:
      with open(log_file, 'r') as f:
        log_data += f.read()
    except FileNotFoundError:
      log_data = f"{time.strftime('%Y-%m-%d %H:%M:%S')} - No log data found"
    return log_data

  def get_entity(self, encoded_email, entity_id):
    with open(f'data/user_data/{encoded_email}/data/entities/{entity_id}/entity_data.json', 'r') as f:
      entity_data = json.loads(f.read())
    return entity_data

  def update_entity(self, encoded_email, entity_id, entity_data):
    with open(f'data/user_data/{encoded_email}/data/entities/{entity_id}/entity_data.json', 'r') as f:
      existing_entity_data = json.loads(f.read())
    for key in entity_data:
      existing_entity_data[key] = entity_data[key]
    new_entity_data = existing_entity_data
    with open(f'data/user_data/{encoded_email}/data/entities/{entity_id}/entity_data.json', 'w') as f:
      f.write(json.dumps(new_entity_data))
    return new_entity_data

  def retrieve_profile(self, encoded_email, profile, entity_id):
    profile_path = f'data/user_data/{encoded_email}/data/entities/{entity_id}/profiles/{profile}.html'
    try:
      with open(profile_path, 'rb') as f:
        profile_data = f.read()
      return profile_data
    except FileNotFoundError:
      return "Profile not found"

  def rename_file(self, encoded_email, filename, entity_id):
    video_folder = f'data/user_data/{encoded_email}/data/entities/{entity_id}/videos/'
    new_filename = str(uuid.uuid4()) + '.mp4'
    os.rename(os.path.join(video_folder, filename), os.path.join(video_folder, new_filename))
    return new_filename

  def check_chunks(self, encoded_email, filename, entity_id):
    filename = filename.split('_')[0]
    video_folder = f'data/user_data/{encoded_email}/data/entities/{entity_id}/videos/'
    all_files = os.listdir(video_folder)
    all_chunks = []
    for file in all_files:
      if file.startswith(filename) and not file.endswith('.mp4'):
        i = file.split('_')[1]
        all_chunks.append(1)
    return len(all_chunks)

  def check_final_chunk(self, encoded_email, filename, num_chunks, entity_id):
    filename = filename.split('_')[0]
    video_folder = f'data/user_data/{encoded_email}/data/entities/{entity_id}/videos/'
    all_files = os.listdir(video_folder)
    all_chunks = []
    for file in all_files:
      if file.startswith(filename) and not file.endswith('.mp4'):
        i = file.split('_')[1]
        all_chunks.append(1)
    completion_percentage = round(len(all_chunks) / int(num_chunks) * 100, 2)
    message = f'{time.strftime('%Y-%m-%d %H:%M:%S')} Chunks Processed: {len(all_chunks)}, Total Chunks: {num_chunks} ({completion_percentage}% Complete)'
    print(message)
    self.write_to_log(encoded_email, entity_id, message)
    return len(all_chunks) == int(num_chunks)

  def reconstruct_video(self, encoded_email, filename, entity_id):
    video_folder = f'data/user_data/{encoded_email}/data/entities/{entity_id}/videos/'
    all_files = os.listdir(video_folder)
    all_chunks = []
    for file in all_files:
      if file.startswith(filename):
        try:
          i = file.split('_')[1]
        except IndexError:
          print(f"IndexError: {file}")
          continue
        all_chunks.append(int(i))
    all_chunks.sort()
    max_chunk = all_chunks[-1]
    video_parts = [f"{filename}_{i}" for i in range(max_chunk + 1)]
    with open(os.path.join(video_folder, filename), 'wb') as output_file:
      for part in video_parts:
        with open(os.path.join(video_folder, part), 'rb') as part_file:
          print(f"Writing {part} to {filename}")
          output_file.write(part_file.read())
        try:
          os.remove(os.path.join(video_folder, part))
        except FileNotFoundError:
          print(f"Possible race condition. Unable to remove file: {part} (is it already removed?)")

  def save_video_chunk(self, encoded_email, chunk, filename, entity_id):
    video_folder = f'data/user_data/{encoded_email}/data/entities/{entity_id}/videos/'
    with open(os.path.join(video_folder, filename), 'wb') as f:
      f.write(chunk)
      message = f"{time.strftime('%Y-%m-%d %H:%M:%S')} Writing chunk for {filename} complete."
      print(message)
      self.write_to_log(encoded_email, entity_id, message)

  def check_user_data_dir_exists(self, encoded_email):
    user_data_path = f'data/user_data/{encoded_email}/data/'
    return os.path.exists(user_data_path)

  def create_user_data_dir(self, encoded_email):
    user_data_path = f'data/user_data/{encoded_email}/data/'
    os.makedirs(user_data_path, exist_ok=True)
    user_data_path = f'data/user_data/{encoded_email}/data/videos/'
    os.makedirs(user_data_path, exist_ok=True)
    user_data_path = f'data/user_data/{encoded_email}/data/profiles/'
    os.makedirs(user_data_path, exist_ok=True)
    user_data_path = f'data/user_data/{encoded_email}/data/entities/'
    os.makedirs(user_data_path, exist_ok=True)
  
  def get_all_videos_for_user(self, encoded_email):
    video_folder = f'data/user_data/{encoded_email}/data/videos/'
    all_videos = []
    try:
      all_files = os.listdir(video_folder)
      for file in all_files:
        if file.endswith('.mp4'):
          all_videos.append(file)
    except FileNotFoundError:
      os.makedirs(video_folder)
    return all_videos

  def get_all_profiles(self, encoded_email, entity_id):
    profile_folder = f'data/user_data/{encoded_email}/data/entities/{entity_id}/profiles'
    all_profiles = []
    try:
      all_files = os.listdir(profile_folder)
      for file in all_files:
        data_dict = {
          'name': file.split('.')[0],
          'name_capitalize': file.split('.')[0].capitalize(),
          }
        all_profiles.append(data_dict)
    except FileNotFoundError:
      os.makedirs(profile_folder)
    return all_profiles

  def display_video_for_user(self, encoded_email, filename, entity_id):
    video_folder = f'data/user_data/{encoded_email}/data/entities/{entity_id}/videos/'
    video_path = os.path.join(video_folder, filename)
    with open(video_path, 'rb') as f:
      video_data = f.read()
    return video_data

  def delete_video(self, filename, encoded_email, entity_id):
    print(f"Deleting {filename} for user {encoded_email}")
    video_folder = f'data/user_data/{encoded_email}/data/entities/{entity_id}/videos/'
    file_path = os.path.join(video_folder, filename)
    os.remove(file_path)

  def delete_entity(self, encoded_email, entity_id):
    entity_folder = f'data/user_data/{encoded_email}/data/entities/{entity_id}'
    shutil.rmtree(entity_folder)

  def get_all_entities_for_user(self, encoded_email):
    entities_folder = f'data/user_data/{encoded_email}/data/entities/'
    all_entities = []
    all_files = os.listdir(entities_folder)
    all_files.sort(key=lambda x: os.path.getctime(os.path.join(entities_folder, x)))
    all_files.reverse()
    for file in all_files:
      all_entities.append(file)
    return all_entities
  
  def get_all_videos_for_entity(self, encoded_email, entity):
    entity_folder = f'data/user_data/{encoded_email}/data/entities/{entity}/videos'
    all_videos = []
    try:
      all_files = os.listdir(entity_folder)
    except FileNotFoundError:
      os.makedirs(entity_folder)
      all_files = []
    for file in all_files:
      if not file.endswith('.mp4'):
        continue
      video_filepath = os.path.join(entity_folder, file)
      video = cv2.VideoCapture(video_filepath)
      frame_count = video.get(cv2.CAP_PROP_FRAME_COUNT)
      fps = video.get(cv2.CAP_PROP_FPS)
      duration = frame_count / fps
      size_MB = round(os.path.getsize(video_filepath) / 1024 / 1024, 2)
      video_metadata = {
        'filename': file,
        'id': file.split('.')[0],
        'size_MB': size_MB,
        'duration': round(duration, 2),
        'frame_count': frame_count,
        'fps': round(fps, 2),
        'est_frames_processed': int(duration)
      }
      all_videos.append(video_metadata)
    return all_videos

  def create_entity(self, encoded_email):
    entity_id = str(uuid.uuid4())
    entity_folder = f'data/user_data/{encoded_email}/data/entities/{entity_id}'
    os.makedirs(entity_folder)
    entity_folder = f'data/user_data/{encoded_email}/data/entities/{entity_id}/videos'
    os.makedirs(entity_folder)
    with open(f'data/defaults/entity.json', 'r') as f:
      default_data = json.loads(f.read())
    with open(f'data/user_data/{encoded_email}/data/entities/{entity_id}/entity_data.json', 'w') as f:
      default_data['created_timestamp'] = time.time()
      default_data['id'] = entity_id
      f.write(json.dumps(default_data))
    return default_data

class HTMLFormatter:
  def __init__(self):
    pass

  def create_video_dict_list(self, all_videos):
    videos_dict_list = []
    for filename in all_videos:
      videos_dict = {}
      videos_dict['filename'] = filename
      videos_dict['uid'] = filename.split('.')[0]
      videos_dict['uri'] = os.path.join(f'/display_video/{filename}')
      videos_dict_list.append(videos_dict)
    return videos_dict_list

  def create_entity_cards(self, encoded_email, all_entities, file_handler):
    html = ''
    with open('data/defaults/entity.json', 'r') as f:
      default_data = json.loads(f.read())
    html += render_template('entity_card_add_new.html', entity=default_data)
    for entity in all_entities:
      with open(f'data/user_data/{encoded_email}/data/entities/{entity}/entity_data.json', 'r') as f:
        entity_data = json.loads(f.read())
      entity_videos = file_handler.get_all_videos_for_entity(encoded_email, entity)
      all_profiles = file_handler.get_all_profiles(encoded_email, entity)
      html += render_template('entity_card.html', entity=entity_data,
                              entity_videos=entity_videos,
                              all_profiles=all_profiles)
    return html