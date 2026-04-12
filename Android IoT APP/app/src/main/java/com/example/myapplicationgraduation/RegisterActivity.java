package com.example.myapplicationgraduation;

import android.app.Activity;
import android.app.Notification;
import android.content.Intent;
import android.os.Bundle;
import android.os.Handler;
import android.os.Message;
import android.view.View;
import android.widget.Button;
import android.widget.EditText;
import android.widget.Toast;

import com.alibaba.fastjson.JSON;
import com.alibaba.fastjson.JSONObject;

import java.util.Properties;

public class RegisterActivity extends Activity {
    private EditText et_Reg_account;
    private EditText et_Reg_password;
    private EditText et_Reg_device_key;
    private Button b_Back_to_login;
    private Button b_Register;

    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_register);
        setTitle("注册");

        et_Reg_account = (EditText) findViewById(R.id.reg_account);
        et_Reg_password = (EditText) findViewById(R.id.reg_password);
        et_Reg_device_key = (EditText) findViewById(R.id.product_key);
        b_Register = (Button) findViewById(R.id.submit);
        b_Back_to_login = (Button)findViewById(R.id.back);

        b_Back_to_login.setOnClickListener(new View.OnClickListener() {
            @Override
            public void onClick(View view) {
                Toast.makeText(RegisterActivity.this,"已离开注册页面",Toast.LENGTH_SHORT).show();
                startActivity(new Intent(RegisterActivity.this,LoginActivity.class));
                finish();
            }
        });

        b_Register.setOnClickListener(new View.OnClickListener() {
            @Override
            public void onClick(View view) {
                new Thread(new Runnable() {
                    @Override
                    public void run() {
                        int state = register();
                        Message message = new Message();
                        Bundle bundle = new Bundle();
                        bundle.putInt("state", state);
                        message.setData(bundle);
                        handler_register.sendMessage(message);
                    }
                }).start();
            }
        });

    }

    Handler handler_register = new Handler() {
        public void handleMessage(Message message) {
            super.handleMessage(message);
            int state = message.getData().getInt("state");
            if (state == 1) {
                Toast.makeText(RegisterActivity.this, "注册成功！", Toast.LENGTH_LONG).show();
            } else if (state == 0) {
                Toast.makeText(RegisterActivity.this, "注册失败！", Toast.LENGTH_LONG).show();
            }
        }
    };

    protected int register() {
        int state = 0;
        try {
            // 读取assets文件夹下的用户配置文件键值对
            Properties properties = new Properties();
            properties.load(getAssets().open("config.properties"));
            String ip = properties.getProperty("ip");
            int port = Integer.parseInt(properties.getProperty("port"));

            String reg_account = et_Reg_account.getText().toString();
            String reg_password = et_Reg_password.getText().toString();

            String device_key = et_Reg_device_key.getText().toString();
            if (device_key.equals(""))
                device_key = "NULL";  // 强行填入字段

            MyComm myComm = new MyComm();
            String reg_data = myComm.format_comm_data("register", JSON.toJSONString(new UserBean(reg_account, reg_password, device_key)), "1");

            MySocket.initSocket(ip, port);
            MySocket.sendInfo(reg_data);
            String response = MySocket.getInfo();
            JSONObject respJson = JSON.parseObject(response);
            state = respJson.getIntValue("status");
        } catch (Exception e) {
            e.printStackTrace();
        } finally {
            return state;
        }
    }

}
