<?php
class Recruit_admin_model extends CI_Model {

	private $db_bot;

	public function __construct()
	{
		parent::__construct();
		// ステップ1で設定した 'bot_db' を読み込む
		$this->db_bot = $this->load->database('bot_db', TRUE);
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
		$this->db_bot->where('id', $id);
		return $this->db_bot->update('recruits', $data);
	}

	/**
	 * 募集情報を削除する
	 */
	public function delete_recruit($id)
	{
		$this->db_bot->where('id', $id);
		return $this->db_bot->delete('recruits');
	}
}