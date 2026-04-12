package com.example.myapplicationgraduation;

import android.content.Intent;
import android.os.Bundle;
import android.os.Handler;
import android.os.Message;
import android.view.View;
import android.widget.Button;
import android.widget.EditText;
import android.widget.Toast;

import androidx.appcompat.app.AppCompatActivity;

import com.alibaba.fastjson.JSON;
import com.alibaba.fastjson.JSONObject;

import java.util.Properties;

public class LoginActivity extends AppCompatActivity {
    private EditText e_Given_account;
    private EditText e_Given_password;
    private Button b_Login;
    private Button b_to_Reg;
    private Button b_to_Dev;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_login);
        setTitle("IoT APP"); //设置登陆页面标题

        e_Given_account = (EditText)findViewById(R.id.given_account);
        e_Given_password = (EditText) findViewById(R.id.given_password);
        b_Login = (Button)findViewById(R.id.login);
        b_to_Reg = (Button)findViewById(R.id.register);
        b_to_Dev = (Button)findViewById(R.id.developer);

        b_to_Reg.setOnClickListener(new View.OnClickListener() {
            @Override
            public void onClick(View v) {
                Toast.makeText(LoginActivity.this,"已转到注册页面",Toast.LENGTH_SHORT).show();
                startActivity(new Intent(LoginActivity.this,RegisterActivity.class));
                finish();
            }
        });

        b_to_Dev.setOnClickListener(new View.OnClickListener() {
            @Override
            public void onClick(View view) {
                startActivity(new Intent(LoginActivity.this,DeveloperActivity.class));
                finish();
            }
        });

        //增加：输入错误处理

        // 单击login按钮开启线程
        b_Login.setOnClickListener(new View.OnClickListener() {
            @Override
            public void onClick(View view) {
                new Thread(new Runnable() {
                    @Override
                    public void run() {
                        int state = login();
                        Message message = new Message();
                        Bundle bundle = new Bundle();
                        bundle.putInt("state", state);
                        message.setData(bundle);
                        handler_login.sendMessage(message);
                    }
                }).start();
            }
        });
    }

    Handler handler_login = new Handler() {
        public void handleMessage(Message message) {
            super.handleMessage(message);
            int state = message.getData().getInt("state");
            if (state == 1) {
                Toast.makeText(LoginActivity.this, "登录成功！", Toast.LENGTH_LONG).show();
                startActivity(new Intent(LoginActivity.this,MainActivity.class));
                finish();
            } else if (state == 0) {
                Toast.makeText(LoginActivity.this, "登录失败！", Toast.LENGTH_LONG).show();
            }
        }
    };


    protected int login() {
        int state = 0;
        try {
            // 读取assets文件夹下的用户配置文件键值对
            Properties properties = new Properties();
            properties.load(getAssets().open("config.properties"));
            String ip = properties.getProperty("ip");
            int port = Integer.parseInt(properties.getProperty("port"));

            // 从用户输入框内获取输入值
            String given_account = e_Given_account.getText().toString();
            String given_password = e_Given_password.getText().toString();

            // 遵循通信格式： 指令码|数据码|状态码
            // String log_data = "login|" + JSON.toJSONString(new UserBean(given_account, given_password, "NULL")) + "|1";
            MyComm myComm = new MyComm();
            String log_data = myComm.format_comm_data("login", JSON.toJSONString(new UserBean(given_account, given_password, "NULL")), "1");

            MySocket.initSocket(ip, port);
            MySocket.sendInfo(log_data);
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