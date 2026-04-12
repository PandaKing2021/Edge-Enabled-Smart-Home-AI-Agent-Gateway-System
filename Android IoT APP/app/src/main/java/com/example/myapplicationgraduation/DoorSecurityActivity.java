package com.example.myapplicationgraduation;

import android.app.Activity;
import android.content.ContentValues;
import android.os.Bundle;
import android.os.Handler;
import android.os.Message;
import android.widget.TextView;

import com.alibaba.fastjson.JSON;
import com.alibaba.fastjson.JSONObject;

import java.text.SimpleDateFormat;
import java.util.Date;
import java.util.Timer;
import java.util.TimerTask;

public class DoorSecurityActivity extends Activity {
    private TextView tv_door_secur_id;
    private TextView tv_door_secur_status;
    private String[] data = {"0","0","0"};

    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_doorsecurity);
        setTitle("智能门禁");

        tv_door_secur_id = (TextView)findViewById(R.id.door_secur_id);
        tv_door_secur_status = (TextView)findViewById(R.id.door_secur_status);

        TimerTask task = new TimerTask() {
            @Override
            public void run() {
                getInfo();
            }
        };
        Timer timer = new Timer();
        timer.scheduleAtFixedRate(task, 1500,1500);
    }

    protected void getInfo(){
        try {
            final String info = MySocket.getInfo();
            new Thread(new Runnable() {
                @Override
                public void run() {
                    Message msg = new Message();
                    Bundle bundle = new Bundle();
                    bundle.putString("info",info);
                    msg.setData(bundle);
                    handler.sendMessage(msg);
                }
            }).start();
        }catch (Exception e){
            e.printStackTrace();
        }
    }

    Handler handler = new Handler(){
        public void handleMessage(Message msg){
            super.handleMessage(msg);
            refreshData(msg.getData().getString("info"));
            refreshViews();
        }
    };

    private void refreshData(String info){
        JSONObject jsonObject = (JSONObject) JSON.parse(info);

        data[0] = jsonObject.getString("Door_Secur_Card_id");
        data[1] = jsonObject.getString("Door_Security_Status");
    }

    private void refreshViews(){
        tv_door_secur_id.setText(data[0]);
        tv_door_secur_status.setText(data[1].equals("1")?"通过":"拒绝");
    }

}
