<?php

namespace App\Controllers;

class Home extends BaseController
{	public function __construct()
	{
		helper('url'); // この行を追加
	}
    public function index(): string
    {
        echo 'test';
        return view('welcome_message');
    }
}
