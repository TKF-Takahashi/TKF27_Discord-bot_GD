<?php
class Recruit_admin_model extends CI_Model {

	private $db_bot;

	public function __construct()
	{
		parent::__construct();
		$this->db_bot = $this->load->database('bot_db', TRUE);
		// ログテーブルの存在を確認し、なければ作成する
		$this->init_log_table();
		// ユーザー情報テーブルの存在を確認し、なければ作成する
		$this->init_users_table();
	}

	/**
	 * ログテーブルを初期化する
	 */
	private function init_log_table()
	{
		if (!$this->db_bot->table_exists('logs')) {
			$this->db_bot->query("
				CREATE TABLE logs (
					id INTEGER PRIMARY KEY AUTOINCREMENT,
					timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
					source TEXT NOT NULL,
					level TEXT NOT NULL,
					message TEXT NOT NULL
				)
			");
		}
	}

	/**
	 * ユーザー情報テーブルを初期化する
	 */
	private function init_users_table()
	{
		if (!$this->db_bot->table_exists('users')) {
			$this->db_bot->query("
				CREATE TABLE users (
					id INTEGER PRIMARY KEY,
					username TEXT NOT NULL,
					last_updated DATETIME DEFAULT CURRENT_TIMESTAMP
				)
			");
		}
	}

	/**
	 * ログを記録する
	 * @param string $level (INFO, WARNING, ERROR)
	 * @param string $message ログメッセージ
	 * @param string $source (BOT, ADMIN)
	 */
	private function _log_change($level, $message, $source = 'ADMIN')
	{
		$data = array(
			'level' => $level,
			'message' => $message,
			'source' => $source
		);
		$this->db_bot->insert('logs', $data);
	}

	/**
	 * 全ての募集情報を取得する
	 */
	public function get_all_recruits()
	{
		return $this->db_bot->order_by('id', 'DESC')->get('recruits')->result_array();
	}

	/**
	 * IDを指定して単一の募集情報を取得する
	 */
	public function get_recruit_by_id($id)
	{
		return $this->db_bot->get_where('recruits', array('id' => $id))->row_array();
	}

	/**
	 * 募集情報を更新する
	 */
	public function update_recruit($id, $data)
	{
		// 変更前のデータを取得
		$before = $this->get_recruit_by_id($id);
		
		$this->db_bot->where('id', $id);
		$result = $this->db_bot->update('recruits', $data);

		if ($result) {
			$this->_log_change('INFO', "Recruit ID: {$id} was updated. Before: " . json_encode($before) . " After: " . json_encode($data));
		}
		return $result;
	}

	/**
	 * 募集情報を削除する
	 */
	public function delete_recruit($id)
	{
		$before = $this->get_recruit_by_id($id);
		$this->db_bot->where('id', $id);
		$result = $this->db_bot->delete('recruits');

		if ($result) {
			$this->_log_change('WARNING', "Recruit ID: {$id} was deleted. Data: " . json_encode($before));
		}
		return $result;
	}

	/**
	 * 設定値を取得する
	 */
	public function get_setting($key)
	{
		return $this->db_bot->get_where('settings', array('key' => $key))->row_array();
	}

	/**
	 * 設定値を保存または更新する
	 */
	public function set_setting($key, $value)
	{
		$before = $this->get_setting($key);
		$data = array(
			'key' => $key,
			'value' => $value
		);
		$this->db_bot->replace('settings', $data);
		$this->_log_change('INFO', "Setting '{$key}' was updated. Before: " . ($before ? $before['value'] : 'NULL') . " After: {$value}");
	}

	/**
	 * データベースをCSV形式でエクスポートする
	 */
	public function export_csv()
	{
		$db_path = $this->db_bot->database;
		$csv_file_path = tempnam(sys_get_temp_dir(), 'csv_export_');
		
		$command = "sqlite3 -header -csv \"{$db_path}\" \"SELECT * FROM recruits;\" > \"{$csv_file_path}\"";
		exec($command);

		return $csv_file_path;
	}

	/**
	 * 全てのログを取得する
	 */
	public function get_all_logs()
	{
		return $this->db_bot->order_by('id', 'DESC')->get('logs')->result_array();
	}
	
	/**
	 * ユーザー情報をDBに保存または更新する
	 */
	public function store_user_info($user_id, $username)
	{
		$data = array(
			'id' => $user_id,
			'username' => $username,
			'last_updated' => date('Y-m-d H:i:s')
		);
		$this->db_bot->replace('users', $data);
	}

	/**
	 * 複数のユーザーIDからユーザー名を取得する
	 */
	public function get_usernames_by_ids($user_ids)
	{
		if (empty($user_ids)) {
			return array();
		}
		$this->db_bot->where_in('id', $user_ids);
		$query = $this->db_bot->get('users');
		$results = $query->result_array();
		
		$users = array();
		foreach ($results as $row) {
			$users[$row['id']] = $row['username'];
		}
		return $users;
	}
}