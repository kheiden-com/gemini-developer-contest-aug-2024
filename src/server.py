from flask import Flask, request, render_template, Response
from ai.utilities import FileHandler
from ai.utilities import HTMLFormatter
from ai.video import VideoLLM
import datetime
import base64


app = Flask(__name__)
file_handler = FileHandler()
html_formatter = HTMLFormatter()

@app.route('/', methods=['GET'])
def root():
  return render_template('install.html')

@app.route('/static/<filename>', methods=['GET'])
def static_file(filename):
  return app.send_static_file(filename)

@app.route('/main.html', methods=['GET'])
def main():
  user_email = request.headers.get('Cf-Access-Authenticated-User-Email')
  encoded_email = base64.b64encode(user_email.encode('utf-8')).decode('utf-8')
  file_handler.create_user_data_dir(encoded_email)
  return render_template('main.html')

@app.route('/entity/<id>/edit', methods=['GET'])
def edit_entity(id):
  user_email = request.headers.get('Cf-Access-Authenticated-User-Email')
  encoded_email = base64.b64encode(user_email.encode('utf-8')).decode('utf-8')
  entity_data = file_handler.get_entity(encoded_email, id)
  return render_template('edit_entity.html', entity=entity_data)

@app.route('/entity/<id>', methods=['PUT'])
def update_entity(id):
  user_email = request.headers.get('Cf-Access-Authenticated-User-Email')
  encoded_email = base64.b64encode(user_email.encode('utf-8')).decode('utf-8')
  entity_data = {
    'name': request.form.get('name'),
    'description': request.form.get('description')
  }
  new_entity_data = file_handler.update_entity(encoded_email, id, entity_data)
  return render_template('view_entity.html', entity=new_entity_data)

@app.route('/entity/<id>/cancel', methods=['GET'])
def cancel_edit_entity(id):
  user_email = request.headers.get('Cf-Access-Authenticated-User-Email')
  encoded_email = base64.b64encode(user_email.encode('utf-8')).decode('utf-8')
  entity_data = file_handler.get_entity(encoded_email, id)
  return render_template('view_entity.html', entity=entity_data)

@app.route('/entity/<id>/collapse', methods=['GET'])
def collapse_entity(id):
  user_email = request.headers.get('Cf-Access-Authenticated-User-Email')
  encoded_email = base64.b64encode(user_email.encode('utf-8')).decode('utf-8')
  entity_data = file_handler.get_entity(encoded_email, id)
  return render_template('entity_collapse.html', entity=entity_data)

@app.route('/entity/<id>', methods=['GET'])
def get_entity_data(id):
  user_email = request.headers.get('Cf-Access-Authenticated-User-Email')
  encoded_email = base64.b64encode(user_email.encode('utf-8')).decode('utf-8')
  entity_data = file_handler.get_entity(encoded_email, id)
  all_profiles = file_handler.get_all_profiles(encoded_email, id)
  return render_template('entity_card.html', entity=entity_data, all_profiles=all_profiles)

@app.route('/delete_entity/<id>', methods=['POST'])
def delete_entity(id):
  user_email = request.headers.get('Cf-Access-Authenticated-User-Email')
  encoded_email = base64.b64encode(user_email.encode('utf-8')).decode('utf-8')
  file_handler.delete_entity(encoded_email, id)
  return ''

@app.route('/delete_video/<entity_id>/<filename>', methods=['POST'])
def delete_video(entity_id, filename):
  user_email = request.headers.get('Cf-Access-Authenticated-User-Email')
  encoded_email = base64.b64encode(user_email.encode('utf-8')).decode('utf-8')
  file_handler.delete_video(filename, encoded_email, entity_id)
  return ''

@app.route('/new_entity', methods=['POST'])
def create_new_entity():
  user_email = request.headers.get('Cf-Access-Authenticated-User-Email')
  encoded_email = base64.b64encode(user_email.encode('utf-8')).decode('utf-8')
  entity_data = file_handler.create_entity(encoded_email)
  return render_template('entity_card.html', entity=entity_data, entity_videos=[])

@app.route('/list_entities', methods=['GET'])
def list_entities():
  user_email = request.headers.get('Cf-Access-Authenticated-User-Email')
  encoded_email = base64.b64encode(user_email.encode('utf-8')).decode('utf-8')
  all_entities = file_handler.get_all_entities_for_user(encoded_email)
  html = html_formatter.create_entity_cards(encoded_email, all_entities, file_handler)
  return html

@app.route('/video', methods=['GET'])
def video():
  print(request.args.get('p'))
  page_num = int(request.args.get('p') or '0')
  next_page_num = page_num + 1
  user_email = request.headers.get('Cf-Access-Authenticated-User-Email')
  encoded_email = base64.b64encode(user_email.encode('utf-8')).decode('utf-8')
  all_videos = file_handler.get_all_videos_for_user(encoded_email)
  if page_num >= len(all_videos):
    return ''
  videos_dict_list = html_formatter.create_video_dict_list([all_videos[page_num]])
  video = videos_dict_list[0]
  all_profiles = file_handler.get_all_profiles(encoded_email, video['uid'])
  html = f"""    <div hx-get="/video?p={next_page_num}"
    hx-trigger="revealed"
    hx-swap="afterend">{render_template('video.html', video=video,
                                        all_profiles=all_profiles)}</div>"""
  return html

@app.route('/display_video/<entity_id>/<filename>', methods=['GET'])
def display_video(entity_id, filename):
  """
  This function will display a video based on the filename provided.

  HTMX will call this function to display the image.

  Args:
    filename (str): The filename of the image.
  """
  print(f"Displaying video: {filename}")
  user_email = request.headers.get('Cf-Access-Authenticated-User-Email')
  encoded_email = base64.b64encode(user_email.encode('utf-8')).decode('utf-8')
  video_data = file_handler.display_video_for_user(encoded_email, filename, entity_id)
  return Response(video_data, mimetype='video/mp4')

@app.route('/process_video/<filename>/<action>', methods=['GET'])
def process_video(filename, action):
  """
  This function will process an video based on the UUID and action provided.

  HTMX will call this function to process the video.

  Args:
    filename (str): The filename of the video.
    action (str): The action to take. Currently supports 'delete'.
  """
  user_email = request.headers.get('Cf-Access-Authenticated-User-Email')
  encoded_email = base64.b64encode(user_email.encode('utf-8')).decode('utf-8')
  if action == 'delete':
    file_handler.delete_video(filename, encoded_email)
    return ''

@app.route('/get_entity_log/<entity_id>', methods=['GET'])
def get_entity_log(entity_id):
  user_email = request.headers.get('Cf-Access-Authenticated-User-Email')
  encoded_email = base64.b64encode(user_email.encode('utf-8')).decode('utf-8')
  log = file_handler.get_entity_log(encoded_email, entity_id)
  return log

@app.route('/populate_iframe/<entity_id>', methods=['GET'])
def populate_iframe(entity_id):
  profile = request.args.get('profile')
  if not profile:
    hide_style = 'display:none;'
    return render_template('iframe.html', hide_style=hide_style, entity_id=entity_id)
  return render_template('iframe.html', entity_id=entity_id, src=f'/profiles/{entity_id}?profile={profile}')

@app.route('/profiles/<entity_id>', methods=['GET'])
def profiles(entity_id):
  user_email = request.headers.get('Cf-Access-Authenticated-User-Email')
  encoded_email = base64.b64encode(user_email.encode('utf-8')).decode('utf-8')
  import random
  i = random.randint(0, 100)
  profile = request.args.get('profile')
  print(f'Getting profile: {profile}')
  allowed_profiles = ['google', 'facebook', 'x', 'instagram', 'tiktok', 'website']
  if profile not in allowed_profiles:
    return render_template('iframe.html', entity_id=entity_id)
  else:
    return file_handler.retrieve_profile(encoded_email, profile, entity_id)

@app.route('/start_video_upload/<entity_id>', methods=['GET'])
def start_video_upload(entity_id):
  user_email = request.headers.get('Cf-Access-Authenticated-User-Email')
  encoded_email = base64.b64encode(user_email.encode('utf-8')).decode('utf-8')
  message = f"{datetime.datetime.now()} Starting video upload..."
  file_handler.write_to_log(encoded_email, entity_id, message)
  return ''

@app.route('/start_inference/<entity_id>', methods=['POST'])
def start_inference(entity_id):
  user_email = request.headers.get('Cf-Access-Authenticated-User-Email')
  encoded_email = base64.b64encode(user_email.encode('utf-8')).decode('utf-8')
  file_handler.remove_erronous_files(encoded_email, entity_id)
  video_llm = VideoLLM(encoded_email, entity_id, file_handler)
  video_llm.async_process_init(encoded_email, entity_id, file_handler)
  entity = file_handler.get_entity(encoded_email, entity_id)
  return entity

@app.route('/log/<entity_id>', methods=['GET'])
def get_log(entity_id):
  user_email = request.headers.get('Cf-Access-Authenticated-User-Email')
  encoded_email = base64.b64encode(user_email.encode('utf-8')).decode('utf-8')
  log = file_handler.get_entity_log(encoded_email, entity_id)
  return log

@app.route('/clear_log/<entity_id>', methods=['POST'])
def clear_log(entity_id):
  user_email = request.headers.get('Cf-Access-Authenticated-User-Email')
  encoded_email = base64.b64encode(user_email.encode('utf-8')).decode('utf-8')
  file_handler.empty_log(encoded_email, entity_id)
  return ''

@app.route('/favicon.ico', methods=['GET'])
def favicon():
  with open('static/favicon.jpg', 'rb') as f:
    return Response(f.read(), mimetype='image/x-icon')

@app.route('/upload', methods=['POST'])
def upload_video():
  user_email = request.headers.get('Cf-Access-Authenticated-User-Email')
  encoded_email = base64.b64encode(user_email.encode('utf-8')).decode('utf-8')
  if request.files.get('uploaded_video'):
    print('Processing chunked video.')
    video = request.files['uploaded_video']
    video_bytes = video.read()
    print(f'Received video chunk with bytes size: {len(video_bytes)}')
    filename = request.form.get('filename') or 'unknown.mp4'
    entity_id = request.form.get('entity_id')
    file_handler.save_video_chunk(encoded_email, video_bytes, filename, entity_id)
    num_chunks = request.form.get('num_chunks')
    file_handler.check_chunks(encoded_email, filename, entity_id)
    final_chunk = file_handler.check_final_chunk(encoded_email, filename, num_chunks, entity_id)
    if final_chunk:
      print('Final chunk received.')
      filename = filename.split('.')[0] + '.mp4'
      file_handler.reconstruct_video(encoded_email, filename, entity_id)
      file_handler.rename_file(encoded_email, filename, entity_id)
      file_handler.write_to_log(encoded_email, entity_id, 'Video upload completed.')
      return 'Final chunk received.'
    else:
      return 'Video chunk saved.'
  else:
    return 'No video file provided', 400

if __name__ == '__main__':
  app.run(host='0.0.0.0', port=4867, debug=True)