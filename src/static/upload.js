function uploadData(entity_id) {
  const chunkSize = 5 * 1024 * 1024; // 5MB
  fileInput = document.getElementById(`video-upload-${entity_id}`);
  const file = fileInput.files[0];
  const fileSize = file.size;
  let offset = 0;

  function uploadChunk(offset) {
    const chunk = file.slice(offset, offset + chunkSize);
    const formData = new FormData();
    formData.append('uploaded_video', chunk);
    const current_chunk = Math.ceil(offset / chunkSize);
    file_name = `${file.name}_${current_chunk}`;
    formData.append('filename', file_name);
    final_chunk = offset + chunk.size >= fileSize ? 'true' : 'false';
    const num_chunks = Math.ceil(fileSize / chunkSize);
    formData.append('num_chunks', num_chunks);
    formData.append('entity_id', entity_id);

    return new Promise((resolve, reject) => {
      const xhr = new XMLHttpRequest();
      xhr.open('POST', '/upload', true);
      xhr.onload = function() {
        if (xhr.status === 200) {
          resolve();
        } else {
          reject(xhr.status);
        }
      };

      xhr.onerror = function() {
        reject('Error uploading file');
      };

      xhr.send(formData);
    });
  }

  async function uploadChunks() {
    const chunks = [];
    let offset = 0;
    const workers = 4;
    const queue = [];

    while (offset < fileSize) {
      queue.push(offset);
      offset += chunkSize;
    }

    async function worker() {
      while (queue.length > 0) {
        const currentOffset = queue.shift();
        try {
          await uploadChunk(currentOffset);
        } catch (error) {
          console.error('Error uploading chunk:', error);
          break; // Stop uploading chunks in case of an error
        }
      }
    }
  
    const workerPromises = [];
    for (let i = 0; i < workers; i++) {
      workerPromises.push(worker());
    }
  
    await Promise.all(workerPromises);
    console.log('All chunks uploaded');
    location.reload();
  }

  uploadChunks();
}

