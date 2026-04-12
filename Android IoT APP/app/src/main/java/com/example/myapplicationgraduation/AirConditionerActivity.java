package com.example.myapplicationgraduation;

import android.app.Activity;
import android.content.ContentValues;
import android.content.Intent;
import android.database.sqlite.SQLiteDatabase;
import android.os.Bundle;
import android.os.Handler;
import android.os.Looper;
import android.os.Message;
import android.view.View;
import android.widget.Button;
import android.widget.SeekBar;
import android.widget.TextView;
import android.widget.Toast;

import com.alibaba.fastjson.JSON;
import com.alibaba.fastjson.JSONObject;

import java.text.SimpleDateFormat;
import java.util.Date;
import java.util.Timer;
import java.util.TimerTask;

public class AirConditionerActivity extends Activity {
    private SQLiteDatabase db;
    private DatabaseHelper databaseHelper;
    private TextView tv_switch_status;
    private TextView tv_temperature_threshold;
    private SeekBar s_temperature_threshold_seekbar;
    private TextView tv_humidity_threshold;
    private SeekBar s_humidity_threshold_seekbar;
    private Button b_light_open;
    private Button b_light_close;

    int temperature_threshold_value = 0;
    int humidity_threshold_value = 0;
    private String[] data = {"0","0","0"};

    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_airconditioner);
        setTitle("智能空调");

        DatabaseHelper databaseHelper = new DatabaseHelper(this,"iot_db",null,1);
        db = databaseHelper.getWritableDatabase();

        tv_switch_status = (TextView) findViewById(R.id.switch_status_view);
        tv_temperature_threshold = (TextView)findViewById(R.id.temperature_threshold_view);
        tv_humidity_threshold = (TextView)findViewById(R.id.humidity_threshold_view);

        s_temperature_threshold_seekbar = (SeekBar)findViewById(R.id.temperature_threshold_seekbar);
        s_humidity_threshold_seekbar = (SeekBar)findViewById(R.id.humidity_threshold_seekbar);

        b_light_open = (Button)findViewById(R.id.light_open);
        b_light_close = (Button)findViewById(R.id.light_close);

        s_temperature_threshold_seekbar.setOnSeekBarChangeListener(new SeekBar.OnSeekBarChangeListener() {
            @Override
            public void onProgressChanged(SeekBar seekBar, int progress, boolean fromUser) {}

            @Override
            public void onStartTrackingTouch(SeekBar seekBar) {}

            @Override
            public void onStopTrackingTouch(SeekBar seekBar) {
                temperature_threshold_value = s_temperature_threshold_seekbar.getProgress();
                new Thread(new Runnable() {
                    @Override
                    public void run() {
                        try {
                            MyComm myComm = new MyComm();
                            MySocket.sendInfo(myComm.format_comm_data("change_temperature_threshold",Integer.toString(temperature_threshold_value),"1"));
                        }catch (Exception e){
                            e.printStackTrace();
                        }
                    }
                }).start();
            }
        });

        s_humidity_threshold_seekbar.setOnSeekBarChangeListener(new SeekBar.OnSeekBarChangeListener() {
            @Override
            public void onProgressChanged(SeekBar seekBar, int progress, boolean fromUser) {}

            @Override
            public void onStartTrackingTouch(SeekBar seekBar) {}

            @Override
            public void onStopTrackingTouch(SeekBar seekBar) {
                humidity_threshold_value = s_humidity_threshold_seekbar.getProgress();
                new Thread(new Runnable() {
                    @Override
                    public void run() {
                        try {
                            MyComm myComm = new MyComm();
                            MySocket.sendInfo(myComm.format_comm_data("change_humidity_threshold",Integer.toString(humidity_threshold_value),"1"));
                        }catch (Exception e){
                            e.printStackTrace();
                        }
                    }
                }).start();
            }
        });

        start_auto_seekBar_view_thread("temperature");
        start_auto_seekBar_view_thread("humidity");

        b_light_open.setOnClickListener(new View.OnClickListener() {
            @Override
            public void onClick(View view) {
                new Thread(new Runnable() {
                    @Override
                    public void run() {
                        try {
                            MyComm myComm = new MyComm();
                            MySocket.sendInfo(myComm.format_comm_data("light_th_open","1","1"));
                        }catch (Exception e){
                            e.printStackTrace();
                        }
                    }
                }).start();
            }
        });

        b_light_close.setOnClickListener(new View.OnClickListener() {
            @Override
            public void onClick(View view) {
                new Thread(new Runnable() {
                    @Override
                    public void run() {
                        try {
                            MyComm myComm = new MyComm();
                            MySocket.sendInfo(myComm.format_comm_data("light_th_close","0","1"));
                        }catch (Exception e){
                            e.printStackTrace();
                        }
                    }
                }).start();
            }
        });

        TimerTask task = new TimerTask() {
            @Override
            public void run() {
                getInfo();
            }
        };
        Timer timer = new Timer();
        timer.scheduleAtFixedRate(task, 1500,1500);
    }

    private void start_auto_seekBar_view_thread(String tv_name) {
        final Handler handler = new Handler(Looper.getMainLooper());
        new Thread(new Runnable() {
            @Override
            public void run() {
                while (true) {
                    handler.post(new Runnable() {
                        @Override
                        public void run() {
                            if (tv_name.equals("temperature"))
                                tv_temperature_threshold.setText(String.valueOf(temperature_threshold_value));
                            else if (tv_name.equals("humidity"))
                                tv_humidity_threshold.setText(String.valueOf(humidity_threshold_value));
                        }
                    });

                    try {
                        Thread.sleep(1); // 更新间隔，例如每秒更新一次
                    } catch (InterruptedException e) {
                        e.printStackTrace();
                    }
                }
            }
        }).start();
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

        data[0] = jsonObject.getString("Light_TH");
        data[1] = jsonObject.getString("Temperature");
        data[2] = jsonObject.getString("Humidity");

        // 插入历史记录数据库
        ContentValues values = new ContentValues();
        SimpleDateFormat format = new SimpleDateFormat("yyyy - MM - dd HH:mm:ss");
        Date time = new Date();
        String d = format.format(time);
        Date date = null;
        try {
            date = format.parse(d);
        }catch (Exception e){
            e.printStackTrace();
        }

        values.put("time", date.getTime());
        values.put("light_th",data[0]);
        values.put("temperature",data[1]);
        values.put("humidity",data[2]);
        db.insert("history_data",null,values);
    }

    private void refreshViews(){
        tv_switch_status.setText(data[0].equals("1")?"开启":"关闭");
    }

}
