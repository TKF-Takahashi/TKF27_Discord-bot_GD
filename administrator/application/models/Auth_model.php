<?php
class Auth_model extends CI_Model {

	private $db_bot;

	public function __construct()
	{
		parent::__construct();
		$this->db_bot = $this->load->database('bot_db', TRUE);
		// [修正] このモデルではログライブラリの読み込みは不要なため削除しました
	}

	public function login($username, $password)
	{
		log_message('debug', 'Auth_model: login function called for user: ' . $username);

		$this->db_bot->where('username', $username);
		$query = $this->db_bot->get('administrators');
		
		if ($query->num_rows() == 1) {
			$user = $query->row_array();
			log_message('debug', 'Auth_model: User found in database.');
			log_message('debug', 'Auth_model: Input Password: ' . $password);
			log_message('debug', 'Auth_model: DB Hash: ' . $user['password']);

			$is_password_correct = password_verify($password, $user['password']);

			log_message('debug', 'Auth_model: password_verify result: ' . ($is_password_correct ? 'TRUE' : 'FALSE'));

			if ($is_password_correct) {
				log_message('debug', 'Auth_model: Password verification successful.');
				return $user;
			} else {
				log_message('debug', 'Auth_model: Password verification FAILED.');
			}
		} else {
			log_message('debug', 'Auth_model: User NOT found in database.');
		}

		return false;
	}
}