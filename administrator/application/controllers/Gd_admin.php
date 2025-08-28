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
				'note' => $this->input->post('note'),
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

		// 修正: データベースから値を取得し、存在しない場合は空文字列を返す
		$setting = $this->recruit_admin_model->get_setting('mentor_role_id');
		$data['mentor_role_id'] = $setting['value'] ?? '';

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
		$backup_file_path = $this->recruit_admin_model->backup_database();
		if ($backup_file_path) {
			force_download($backup_file_path, NULL);
		} else {
			// エラー処理
			show_error('データベースのバックアップに失敗しました。');
		}
	}
}