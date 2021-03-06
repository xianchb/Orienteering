package com.nctucs.orienteering.project.album;

import android.app.Activity;
import android.app.AlertDialog;
import android.content.Intent;
import android.content.SharedPreferences;
import android.os.Bundle;
import android.os.Handler;
import android.os.Message;
import android.support.v4.app.FragmentActivity;
import android.support.v4.app.FragmentTabHost;
import android.util.Log;
import android.view.LayoutInflater;
import android.view.View;
import android.widget.Button;
import android.widget.TextView;

import com.nctucs.orienteering.project.HttpConnection.HttpConnection;
import com.nctucs.orienteering.project.JSONMsg.JSONType;
import com.nctucs.orienteering.project.R;
import com.nctucs.orienteering.project.tcpSocket.tcpSocket;

import org.json.JSONObject;

/**
 * Created by Shamrock on 2015/4/10.
 */
public class ActivityMain extends FragmentActivity {

    private boolean isNewGame;
    private AlertDialog alert;
    SharedPreferences sharedPreferences;
    String token;

    FragmentTabHost tabHost;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_main);

        tabHost = (FragmentTabHost) findViewById( android.R.id.tabhost );
        SetTabs();
        sharedPreferences = getSharedPreferences( "userData" , MODE_PRIVATE );
        token = sharedPreferences.getString("token", null);
        Intent intent = getIntent();
        isNewGame = intent.getBooleanExtra("isNewGame", true );
        if ( isNewGame ){
            sharedPreferences.edit().putInt("msgCnt", 0).apply();
            sharedPreferences.edit().putInt("hintCnt", 0).apply();
            sharedPreferences.edit().putInt("keyCnt", 0).apply();
            sharedPreferences.edit().putBoolean("initHint" , false).apply();
        }
        new GetHintThread().start();
    }

    private Handler handler = new Handler(){
        @Override
        public void handleMessage(Message msg) {
            super.handleMessage(msg);
            try {
                Bundle bundle = msg.getData();
                JSONObject json = new JSONObject(bundle.getString("json"));
                int hintCnt = json.getInt( "hintCnt" );
                AlertDialog.Builder builder = new AlertDialog.Builder( ActivityMain.this );
                LayoutInflater inflater = getLayoutInflater();
                View v = inflater.inflate( R.layout.dialog_hint , null );

                if ( !sharedPreferences.contains("initHint") || sharedPreferences.getBoolean("initHint" , false) == false ) {

                    int oriHintCnt = sharedPreferences.getInt("hintCnt", 0);
                    for (int i = 0; i < hintCnt; i++)
                        sharedPreferences.edit().putString("hint" + (i + oriHintCnt), json.getString("hint" + i)).apply();

                    Log.e("putted", json.getString("hint0"));

                    sharedPreferences.edit().putInt("hintCnt", oriHintCnt + hintCnt).apply();
                    sharedPreferences.edit().putBoolean( "initHint" , true ).apply();
                }


                String str = "You've got some hint, go check it out!";
                //for ( int i = 0 ; i < hintCnt ; i++ ) {
                //    str += json.getString("hint" + i) + "\n";

                //}
                ( (TextView)v.findViewById( R.id.text_hint_content ) ).setText( str );
                ( (Button)v.findViewById( R.id.dialog_button ) ).setOnClickListener(
                new View.OnClickListener() {
                    @Override
                    public void onClick(View v) {
                        alert.dismiss();
                    }
                }
                );
                builder.setView( v );
                alert = builder.create();
                alert.show();


            }
            catch ( Exception e ){
                e.printStackTrace();
            }
        }
    };


    private class GetHintThread extends Thread implements Runnable{
            @Override
            public void run () {
                try {
                    HttpConnection connection = new HttpConnection();
                    //tcpSocket socket = new tcpSocket();
                    JSONObject json = new JSONType(1);
                    json.put("token", token);
                    connection.send(json);
                    //socket.send(json);
                    JSONObject result = connection.recieve();
                    //JSONObject result = socket.recieve();

                    Message msg = new Message();
                    Bundle bundle = new Bundle();
                    bundle.putString( "json" , result.toString() );
                    msg.setData( bundle );
                    handler.sendMessage(msg);

                }
                catch ( Exception e ){
                    e.printStackTrace();
                }


            }
    }

    private void SetTabs(){


        tabHost.setup(this, getSupportFragmentManager(), R.id.tab_real_content);
        tabHost.setCurrentTab(0);

        tabHost.addTab(tabHost.newTabSpec("遊戲畫面").setIndicator("遊戲畫面"), FragmentGoogleMap.class , null);
        tabHost.addTab(tabHost.newTabSpec("提示").setIndicator("提示") , FragmentMyHint.class , null );
        tabHost.addTab(tabHost.newTabSpec("留言").setIndicator("留言") , FragmentLeaveMessage.class , null );
        tabHost.addTab(tabHost.newTabSpec("鑰匙").setIndicator("鑰匙") , FragmentMyKey.class , null);
    }

}
