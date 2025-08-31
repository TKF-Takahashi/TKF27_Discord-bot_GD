<?php
defined('BASEPATH') OR exit('No direct script access allowed');

class Gd_admin extends CI_Controller {

	public function __construct()
	{
		parent::__construct();
		// ログインチェック
		$this->load->library('session');
		if (!$this->session->userdata('is_logged_in')) {
            redirect('auth/login');
        }

		$this->load->model('recruit_admin_model');
		$this->load->helper('url');
		$this->load->helper('form');
		$this->load->helper('download');
	}

	private function _check_admin()
    {
        if ($this->session->userdata('role') !== 'admin') {
            show_error('You do not have permission to access this page.', 403);
            return false;
        }
        return true;
    }

	public function index()
	{
		$data['title'] = '募集一覧';
		$data['breadcrumb'] = '募集一覧';
		$data['recruits'] = $this->recruit_admin_model->get_all_recruits();

		$this->load->view('templates/header', $data);
		$this->load->view('gd_admin/list', $data);
		$this->load->view('templates/footer');
	}

	public function edit($id)
	{
		if (!$this->_check_admin()) return;

		$this->load->library('form_validation');
		$this->form_validation->set_rules('date_s', '日時', 'required');
		// ... 他のバリデーションルールもここに追加 ...

		if ($this->form_validation->run() === FALSE) {
			$data['title'] = '募集編集';
			$data['breadcrumb'] = '募集一覧 &gt; 編集';
			$data['recruit'] = $this->recruit_admin_model->get_recruit_by_id($id);
			if (empty($data['recruit'])) {
				show_404();
			}
			$this->load->view('templates/header', $data);
			$this->load->view('gd_admin/edit', $data);
			$this->load->view('templates/footer');
		} else {
			$update_data = [
				'date_s' => $this->input->post('date_s'),
				'place' => $this->input->post('place'),
				'max_people' => $this->input->post('max_people'),
				'message' => $this->input->post('message'),
				'mentor_needed' => $this->input->post('mentor_needed') ? 1 : 0,
				'industry' => $this->input->post('industry'),
				'participants' => $this->input->post('participants')
			];
			$this->recruit_admin_model->update_recruit($id, $update_data);
			redirect('gd_admin');
		}
	}

	public function delete($id)
	{
		if (!$this->_check_admin()) return;
		$this->recruit_admin_model->delete_recruit($id);
		redirect('gd_admin');
	}

	public function settings()
	{
		$data['title'] = 'ボット設定';
		$data['breadcrumb'] = 'ボット設定';

		if ($this->input->post() && $this->_check_admin()) {
			$mentor_role_id = $this->input->post('mentor_role_id');
			$this->recruit_admin_model->set_setting('mentor_role_id', $mentor_role_id);
			redirect('gd_admin/settings');
		}
		
		$setting = $this->recruit_admin_model->get_setting('mentor_role_id');
		$data['mentor_role_id'] = $setting ? $setting['value'] : '';

		$this->load->view('templates/header', $data);
		$this->load->view('gd_admin/settings', $data);
		$this->load->view('templates/footer');
	}

	public function update()
	{
		$data['title'] = 'アップデート';
		$data['breadcrumb'] = 'アップデート';
		$this->load->view('templates/header', $data);
		$this->load->view('gd_admin/update', $data);
		$this->load->view('templates/footer');
	}

	public function backup()
	{
		if (!$this->_check_admin()) return;
		$database = $this->load->database('bot_db', TRUE);
		$db_path = $database->database;
		$db_name = basename($db_path);
		$data = file_get_contents($db_path);
		$name = 'db-backup-' . date('Y-m-d_H-i-s') . '-' . $db_name;
		force_download($name, $data);
	}

	public function export_csv()
	{
		if (!$this->_check_admin()) return;
		$this->load->helper('file');
		$csv_file_path = $this->recruit_admin_model->export_csv();
		if (file_exists($csv_file_path)) {
			$file_name = 'recruits_export_' . date('Y-m-d_H-i-s') . '.csv';
			$data = "\xEF\xBB\xBF" . file_get_contents($csv_file_path);
			force_download($file_name, $data);
			unlink($csv_file_path);
		} else {
			show_error('CSVファイルの作成に失敗しました。');
		}
	}
}