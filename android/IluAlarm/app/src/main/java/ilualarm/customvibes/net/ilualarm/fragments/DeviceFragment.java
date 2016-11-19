package ilualarm.customvibes.net.ilualarm.fragments;

import android.content.Context;
import android.graphics.Color;
import android.os.Bundle;
import android.support.design.widget.Snackbar;
import android.support.v4.app.Fragment;
import android.view.LayoutInflater;
import android.view.View;
import android.view.ViewGroup;
import android.widget.Button;
import android.widget.EditText;
import android.widget.SeekBar;

import com.larswerkman.holocolorpicker.ColorPicker;

import java.io.IOException;

import ilualarm.customvibes.net.ilualarm.R;
import ilualarm.customvibes.net.ilualarm.model.RGB;
import ilualarm.customvibes.net.ilualarm.model.Text;
import ilualarm.customvibes.net.ilualarm.model.Volume;
import ilualarm.customvibes.net.ilualarm.rest.IluAlarm;
import ilualarm.customvibes.net.ilualarm.rest.IluAlarmConnection;
import ilualarm.customvibes.net.ilualarm.rest.IluAlarmResponse;
import retrofit.Call;
import retrofit.Response;

/**
 * A fragment with a Google +1 button.
 * Activities that contain this fragment must implement the
 * {@link DeviceFragmentListener} interface
 * to handle interaction events.
 * Use the {@link DeviceFragment#newInstance} factory method to
 * create an instance of this fragment.
 */
public class DeviceFragment extends Fragment {
    private Button saveBtn;

    private DeviceFragmentListener mListener;
    private ColorPicker colorPicker;
    private EditText textView;
    private View view;
    private IluAlarmConnection conn;
    private SeekBar volume;

    public DeviceFragment() {
        // Required empty public constructor
    }

    /**
     * Use this factory method to create a new instance of
     * this fragment using the provided parameters.
     *
     * @param param1 Parameter 1.
     * @param param2 Parameter 2.
     * @return A new instance of fragment DeviceFragment.
     */
    // TODO: Rename and change types and number of parameters
    public static DeviceFragment newInstance(String param1, String param2) {
        DeviceFragment fragment = new DeviceFragment();
        Bundle args = new Bundle();
        fragment.setArguments(args);
        return fragment;
    }

    @Override
    public void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        if (getArguments() != null) {

        }
    }

    @Override
    public View onCreateView(LayoutInflater inflater, ViewGroup container,
                             Bundle savedInstanceState) {
        // Inflate the layout for this fragment
        view = inflater.inflate(R.layout.fragment_device, container, false);

        colorPicker = (ColorPicker) view.findViewById(R.id.color_picker);

        //Find the +1 button
        saveBtn = (Button) view.findViewById(R.id.save_btn);

        textView = (EditText)view.findViewById(R.id.text);

        volume = (SeekBar)view.findViewById(R.id.seek_volume);

        saveBtn.setOnClickListener(new View.OnClickListener() {
            @Override
            public void onClick(View v) {
                final String str = textView.getText().toString();
                conn.addCommand(new IluAlarmConnection.IluConnectionJob() {
                    @Override
                    public Response doCall(IluAlarm conn) throws IOException {
                        Text text = new Text();
                        text.setText(str);
                        retrofit.Call<IluAlarmResponse> call = conn.setText(text);
                        return call.execute();
                    }

                    @Override
                    public void onSuccess(Object data) {
                        getActivity().runOnUiThread(new Runnable() {
                            @Override
                            public void run() {
                                Snackbar.make(view, "Text set!", Snackbar.LENGTH_LONG)
                                        .setAction("Action", null).show();
                            }
                        });
                    }

                    @Override
                    public void onError(Exception e) {
                        getActivity().runOnUiThread(new Runnable() {
                            @Override
                            public void run() {
                                Snackbar.make(view, "Unable to set text", Snackbar.LENGTH_LONG)
                                        .setAction("Action", null).show();
                            }
                        });
                    }
                });
            }
        });

        colorPicker.setOnColorSelectedListener(new ColorPicker.OnColorSelectedListener() {
            @Override
            public void onColorSelected(final int color) {
                conn.addCommand(new IluAlarmConnection.IluConnectionJob() {
                    @Override
                    public Response doCall(IluAlarm conn) throws IOException {
                        RGB rgb = new RGB(Color.red(color), Color.green(color), Color.blue(color));
                        retrofit.Call<IluAlarmResponse> call = conn.setColor(rgb);
                        return call.execute();
                    }

                    @Override
                    public void onSuccess(Object data) {
                        getActivity().runOnUiThread(new Runnable() {
                            @Override
                            public void run() {
                                Snackbar.make(view, "Color set!", Snackbar.LENGTH_LONG)
                                        .setAction("Action", null).show();

                                colorPicker.setOldCenterColor(color);
                                colorPicker.setNewCenterColor(color);
                            }
                        });
                    }

                    @Override
                    public void onError(Exception e) {
                        getActivity().runOnUiThread(new Runnable() {
                            @Override
                            public void run() {
                                Snackbar.make(view, "Unable to set color", Snackbar.LENGTH_LONG)
                                        .setAction("Action", null).show();
                            }
                        });
                    }
                });
            }
        });

        volume.setOnSeekBarChangeListener(new SeekBar.OnSeekBarChangeListener() {
            @Override
            public void onProgressChanged(SeekBar seekBar, final int progress, boolean fromUser) {
                conn.addCommand(new IluAlarmConnection.IluConnectionJob() {
                    @Override
                    public Response doCall(IluAlarm conn) throws IOException {
                        Volume volume = new Volume();
                        volume.setVolume(progress);
                        retrofit.Call<IluAlarmResponse> call = conn.setVolume(volume);
                        return call.execute();
                    }

                    @Override
                    public void onSuccess(Object data) {
                        getActivity().runOnUiThread(new Runnable() {
                            @Override
                            public void run() {
                                Snackbar.make(view, "Volume set!", Snackbar.LENGTH_LONG)
                                        .setAction("Action", null).show();
                            }
                        });
                    }

                    @Override
                    public void onError(Exception e) {
                        getActivity().runOnUiThread(new Runnable() {
                            @Override
                            public void run() {
                                Snackbar.make(view, "Unable to set volume", Snackbar.LENGTH_LONG)
                                        .setAction("Action", null).show();
                            }
                        });
                    }
                });
            }

            @Override
            public void onStartTrackingTouch(SeekBar seekBar) {

            }

            @Override
            public void onStopTrackingTouch(SeekBar seekBar) {

            }
        });

        return view;
    }

    private void updateTask() {

        conn.addCommand(new IluAlarmConnection.IluConnectionJob<RGB>() {
            @Override
            public Response doCall(IluAlarm conn) throws IOException {
                retrofit.Call<IluAlarmResponse<RGB>> color = conn.getColor();
                return color.execute();
            }

            @Override
            public void onSuccess(final RGB body) {
                getActivity().runOnUiThread(new Runnable() {
                    @Override
                    public void run() {
                        if (colorPicker != null) {
                            int c = body.getColor();
                            colorPicker.setColor(c);
                            colorPicker.setOldCenterColor(c);
                            colorPicker.setNewCenterColor(c);
                        }
                    }
                });
            }

            @Override
            public void onError(Exception e) {
                getActivity().runOnUiThread(
                        new Runnable() {
                            @Override
                            public void run() {
                                Snackbar.make(view, "Unable to get color", Snackbar.LENGTH_LONG)
                                        .setAction("Action", null).show();
                            }
                        });

               retry(getContext(), conn);
            }
        });

        conn.addCommand(new IluAlarmConnection.IluConnectionJob<Text>() {

            @Override
            public Response doCall(IluAlarm conn) throws IOException {
                retrofit.Call<IluAlarmResponse<Text>> text = conn.getText();
                return text.execute();
            }

            @Override
            public void onSuccess(final Text textData) {
                getActivity().runOnUiThread(new Runnable() {
                    @Override
                    public void run() {
                        if (textView != null) {
                            textView.setText(textData.getText());
                        }
                    }
                });
            }

            @Override
            public void onError(Exception e) {
                Snackbar.make(view, "Unable to get text", Snackbar.LENGTH_LONG)
                        .setAction("Action", null).show();

                retry(getContext(), conn);

            }
        });

        conn.addCommand(new IluAlarmConnection.IluConnectionJob<Volume>() {
            @Override
            public Response doCall(IluAlarm conn) throws IOException {
                Call<IluAlarmResponse<Volume>> volume = conn.getVolume();
                return volume.execute();
            }

            @Override
            public void onSuccess(final Volume data) {
                getActivity().runOnUiThread(new Runnable() {
                    @Override
                    public void run() {
                        volume.setProgress(data.getVolume());
                    }
                });
            }

            @Override
            public void onError(Exception e) {

            }
        });

    }

    @Override
    public void onResume() {
        super.onResume();

        conn = new IluAlarmConnection(getContext());
        updateTask();
    }

    @Override
    public void onPause() {
        super.onPause();

        conn.purgeAll();
        conn = null;
    }


    @Override
    public void onAttach(Context context) {
        super.onAttach(context);
        if (context instanceof DeviceFragmentListener) {
            mListener = (DeviceFragmentListener) context;
        } else {
            throw new RuntimeException(context.toString()
                    + " must implement DeviceFragmentListener");
        }
    }

    @Override
    public void onDetach() {
        super.onDetach();
        mListener = null;
    }

    /**
     * This interface must be implemented by activities that contain this
     * fragment to allow an interaction in this fragment to be communicated
     * to the activity and potentially other fragments contained in that
     * activity.
     * <p/>
     * See the Android Training lesson <a href=
     * "http://developer.android.com/training/basics/fragments/communicating.html"
     * >Communicating with Other Fragments</a> for more information.
     */
    public interface DeviceFragmentListener {

    }

}
