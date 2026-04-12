package com.example.myapplicationgraduation;

import android.app.Activity;
import android.content.Intent;
import android.os.Bundle;
import android.view.View;
import android.widget.Button;
import android.widget.EditText;
import android.widget.Toast;

import java.io.IOException;
import java.io.InputStream;
import java.io.OutputStream;
import java.util.Properties;

public class DeveloperActivity extends Activity {
    private EditText et_Ip;
    private EditText et_Port;
    private Button b_Back_to_login;
    private Button b_Submit;
    private ConfigPropertiesEditor configEditor = new ConfigPropertiesEditor();

    protected void onCreate(Bundle savedInstanceState) {
    super.onCreate(savedInstanceState);
    setContentView(R.layout.activity_developer);
    setTitle("开发者选项");

    et_Ip = (EditText)findViewById(R.id.ip);
    et_Port = (EditText)findViewById(R.id.port);
    b_Back_to_login = (Button)findViewById(R.id.back_to_main);
    b_Submit = (Button)findViewById(R.id.submit);

    b_Back_to_login.setOnClickListener(new View.OnClickListener() {
        @Override
        public void onClick(View view) {
            startActivity(new Intent(DeveloperActivity.this,LoginActivity.class));
            finish();
        }
    });

    b_Submit.setOnClickListener(new View.OnClickListener() {
        @Override
        public void onClick(View view) {
            String ip = et_Ip.getText().toString();
            String port = et_Port.getText().toString();

            try {
                // 读取配置文件
                configEditor.readProperties();

                // 修改配置文件中的键值对
                configEditor.writeProperties("ip", ip);
                configEditor.writeProperties("port", port);
            } catch (Exception e) {
                e.printStackTrace();
            }
        }
    });


    }

}
