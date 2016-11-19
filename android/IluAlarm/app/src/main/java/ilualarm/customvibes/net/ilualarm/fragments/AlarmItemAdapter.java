package ilualarm.customvibes.net.ilualarm.fragments;

import android.graphics.Color;
import android.support.v7.widget.RecyclerView;
import android.view.LayoutInflater;
import android.view.View;
import android.view.ViewGroup;
import android.widget.TextView;

import java.text.SimpleDateFormat;
import java.util.ArrayList;
import java.util.Calendar;
import java.util.List;

import ilualarm.customvibes.net.ilualarm.R;
import ilualarm.customvibes.net.ilualarm.model.Alarm;

public class AlarmItemAdapter extends RecyclerView.Adapter<AlarmItemAdapter.ViewHolder> {

    private final List<Alarm> mValues;
    private final AlarmsFragment.AlarmsFragmentListener mListener;

    public AlarmItemAdapter(AlarmsFragment.AlarmsFragmentListener listener) {
        mValues = new ArrayList<>();
        mListener = listener;
    }

    public void setValues(List<Alarm> alarms) {
        this.mValues.clear();
        this.mValues.addAll(alarms);
        this.notifyDataSetChanged();
    }

    @Override
    public ViewHolder onCreateViewHolder(ViewGroup parent, int viewType) {
        View view = LayoutInflater.from(parent.getContext())
                .inflate(R.layout.alarm_item, parent, false);
        return new ViewHolder(view);
    }

    final SimpleDateFormat df = new SimpleDateFormat("dd/MM/yyyy");
    final SimpleDateFormat tf = new SimpleDateFormat("HH:mm");

    private String getAlarmText(Alarm alarm) {
        Calendar calendar = Calendar.getInstance();

        long missing = alarm.getTime().getTime() - calendar.getTime().getTime();

        return df.format(alarm.getTime()) + " (" + String.valueOf(missing / 1000l) + " seconds)";
    }

    @Override
    public void onBindViewHolder(final ViewHolder holder, final int position) {

        holder.mItem = mValues.get(position);
        if (holder.mItem.getTime() != null) {
            holder.time.setText(tf.format(holder.mItem.getTime().getTime()));
            holder.date.setText(df.format(holder.mItem.getTime().getTime()));
        }
        else {
            if (holder.mItem.getSetTime() != null) {
                holder.time.setText(tf.format(holder.mItem.getSetTime().getTime()));
                holder.date.setText(df.format(holder.mItem.getSetTime().getTime()));
            }
            else {
                holder.time.setText("??");
                holder.date.setText("??");
            }
        }
        holder.name.setText(holder.mItem.getMessage());
        holder.mView.setBackgroundColor(holder.mView.getContext().getResources().getColor(holder.mItem.isEnabled() ? R.color.alarm_enabled : R.color.alarm_disabled));

        holder.mContentView.setText("Repeat: " + holder.mItem.getRepeatEvery());

        holder.mView.setOnClickListener(new View.OnClickListener() {
            @Override
            public void onClick(View v) {
                if (null != mListener) {
                    mListener.editAlarm(mValues.get(position));

                }
            }
        });
    }

    @Override
    public int getItemCount() {
        return mValues.size();
    }

    public class ViewHolder extends RecyclerView.ViewHolder {
        public final View mView;
        public final TextView time;
        public final TextView mContentView;
        private final TextView name;
        private final TextView date;
        public Alarm mItem;

        public ViewHolder(View view) {
            super(view);
            mView = view;
            time = (TextView) view.findViewById(R.id.time);
            date = (TextView) view.findViewById(R.id.date);
            name = (TextView) view.findViewById(R.id.name);
            mContentView = (TextView) view.findViewById(R.id.content);
        }

        @Override
        public String toString() {
            return super.toString() + " '" + mContentView.getText() + "'" ;
        }
    }
}
