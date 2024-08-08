function toggle_table_visibility(table_id) {
  const table = document.getElementById(table_id);
  table.style.display = table.style.display === 'none' ? 'block' : 'none';
}