<?php
defined('BASEPATH') OR exit('No direct script access allowed');

class Gd_admin extends CI_Controller {

	public function __construct()
	{
		parent::__construct();
		$this->load->model('recruit_admin_model');
		$this->load->helper('url'); // URLヘルパーをロード
		$this->load->helper('form'); // フォームヘルパーをロード
		$this->load->helper('download'); // downloadヘルパーをロード
	}

	/**
	 * 募集一覧ページ
	 */
	public function index()
	{
		$data['recruits'] = $this->recruit_admin_model->get_all_recruits();
		$this->load->view('gd_admin/list', $data);
	}

	/**
	 * 募集編集ページ
	 */
	public function edit($id)
	{
		// フォームが送信された場合 (POST)
		if ($this->input->post()) {
			$update_data = array(
				'date_s' => $this->input->post('date_s'),
				'place' => $this->input->post('place'),
				'max_people' => $this->input->post('max_people'),
				// 修正: データベースの新しいカラムに対応
				'message' => $this->input->post('message'),
				'mentor_needed' => $this->input->post('mentor_needed') ? 1 : 0,
				'industry' => $this->input->post('industry'),
				'participants' => $this->input->post('participants')
			);
			$this->recruit_admin_model->update_recruit($id, $update_data);
			redirect('gd_admin'); // 一覧ページにリダイレクト
		} else {
			// 通常のページ表示 (GET)
			$data['recruit'] = $this->recruit_admin_model->get_recruit_by_id($id);
			if (empty($data['recruit'])) {
				show_404();
			}
			$this->load->view('gd_admin/edit', $data);
		}
	}

	/**
	 * 募集削除処理
	 */
	public function delete($id)
	{
		$this->recruit_admin_model->delete_recruit($id);
		redirect('gd_admin'); // 一覧ページにリダイレクト
	}

	/**
	 * 設定ページ
	 */
	public function settings()
	{
		if ($this->input->post()) {
			$mentor_role_id = $this->input->post('mentor_role_id');
			$this->recruit_admin_model->set_setting('mentor_role_id', $mentor_role_id);
			redirect('gd_admin/settings');
		}
		
		$setting = $this->recruit_admin_model->get_setting('mentor_role_id');
		if ($setting) {
			$data['mentor_role_id'] = $setting['value'];
		} else {
			$data['mentor_role_id'] = '';
		}

		$this->load->view('gd_admin/settings', $data);
	}

	/**
	 * アップデート関連ページ
	 */
	public function update()
	{
		$this->load->view('gd_admin/update');
	}

	/**
	 * データベースバックアップのダウンロード
	 */
	public function backup()
	{
		// データベース設定を読み込む
		$database = $this->load->database('bot_db', TRUE);
		$db_path = $database->database;
		$db_name = basename($db_path);

		// ファイルを読み込んで直接ダウンロード
		$data = file_get_contents($db_path);
		$name = 'db-backup-' . date('Y-m-d_H-i-s') . '-' . $db_name;
		force_download($name, $data);
	}

	/**
	 * データベースをCSVでダウンロード
	 */
	public function export_csv()
	{
		$this->load->helper('file');
		$csv_file_path = $this->recruit_admin_model->export_csv();
		if (file_exists($csv_file_path)) {
			$file_name = 'recruits_export_' . date('Y-m-d_H-i-s') . '.csv';
			// BOM付きUTF-8に変換
			$data = "\xEF\xBB\xBF" . file_get_contents($csv_file_path);
			force_download($file_name, $data);
			unlink($csv_file_path); // 一時ファイルを削除
		} else {
			show_error('CSVファイルの作成に失敗しました。');
		}
	}
}