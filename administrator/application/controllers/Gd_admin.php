// administrator/controllers/Gd_admin.php
<?php
defined('BASEPATH') OR exit('No direct script access allowed');

class Gd_admin extends CI_Controller {

	public function __construct()
	{
		parent::__construct();
		$this->load->model('recruit_admin_model');
		$this->load->helper('url'); // URLヘルパーをロード
		$this->load->helper('form'); // フォームヘルパーをロード
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
				'message' => $this->input->post('message'),
				'mentor_needed' => $this->input->post('mentor_needed') ? 1 : 0,
				'industry' => $this->input->post('industry'),
				'participants' => $this->input->post('participants')
			);
			$this->recruit_admin_model->update_recruit($id, $update_data);
			redirect('gd_admin'); // 一覧ページにリダイレクト
		}

		// 通常のページ表示 (GET)
		$data['recruit'] = $this->recruit_admin_model->get_recruit_by_id($id);
		if (empty($data['recruit'])) {
			show_404();
		}
		$this->load->view('gd_admin/edit', $data);
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
+
		$data['mentor_role_id'] = $this->recruit_admin_model->get_setting('mentor_role_id')['value'] ?? '';
		$this->load->view('gd_admin/settings', $data);
	}
}