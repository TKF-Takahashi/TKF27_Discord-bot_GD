<?php
class Recruit_admin_model extends CI_Model {

	public function __construct()
	{
		parent::__construct();
		$this->load->database('bot_db');
	}

	public function get_all_recruits()
	{
		$query = $this->db->get('recruits');
		return $query->result_array();
	}

	public function get_recruit_by_id($id)
	{
		$query = $this->db->get_where('recruits', array('id' => $id));
		return $query->row_array();
	}

	public function update_recruit($id, $data)
	{
		$this->db->where('id', $id);
		return $this->db->update('recruits', $data);
	}

	public function delete_recruit($id)
	{
		return $this->db->delete('recruits', array('id' => $id));
	}

	public function get_setting($name)
	{
		$query = $this->db->get_where('settings', array('name' => $name));
		$result = $query->row_array();
		return $result ? $result['value'] : null;
	}

	public function set_setting($name, $value)
	{
		$data = array('name' => $name);
		$this->db->where($data);
		$query = $this->db->get('settings');

		if ($query->num_rows() > 0) {
			$this->db->where('name', $name);
			$this->db->update('settings', array('value' => $value));
		} else {
			$this->db->insert('settings', array('name' => $name, 'value' => $value));
		}
		
		// ▼▼▼【追加】設定変更時にキャッシュを削除 ▼▼▼
		$this->db->cache_delete('gd_admin', 'settings');
		// ▲▲▲【追加】ここまで ▲▲▲
	}

	public function get_all_logs()
	{
		$this->db->order_by('timestamp', 'DESC');
		$query = $this->db->get('logs');
		return $query->result_array();
	}

	public function get_usernames_by_ids($user_ids)
	{
		if (empty($user_ids)) {
			return [];
		}
		$this->db->where_in('id', $user_ids);
		$query = $this->db->get('users');
		$results = $query->result_array();
		$users = [];
		foreach ($results as $row) {
			$users[$row['id']] = $row['username'];
		}
		return $users;
	}

	public function store_user_info($id, $username)
	{
		$this->db->replace('users', ['id' => $id, 'username' => $username]);
	}

	public function export_csv()
	{
		$this->load->dbutil();
		$query = $this->db->query("SELECT * FROM recruits");
		$delimiter = ",";
		$newline = "\r\n";
		$enclosure = '"';
		$csv_data = $this->dbutil->csv_from_result($query, $delimiter, $newline, $enclosure);

		$this->load->helper('file');
		$temp_file = tempnam(sys_get_temp_dir(), 'csv_export');
		if (!write_file($temp_file, $csv_data)) {
			return false;
		}
		return $temp_file;
	}
}