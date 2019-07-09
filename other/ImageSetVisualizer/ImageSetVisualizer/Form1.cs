using System;
using System.IO;
using System.Collections.Generic;
using System.ComponentModel;
using System.Data;
using System.Drawing;
using System.Linq;
using System.Text;
using System.Threading.Tasks;
using System.Windows.Forms;

using OxyPlot;
using OxyPlot.Axes;
using OxyPlot.Series;
using System.Drawing.Drawing2D;
using System.Drawing.Imaging;

namespace ImageSetVisualizer
{
    public partial class Form1 : Form
    {
        const int PLOTSPREAD = 100;

        List<ImageFile> allFiles = new List<ImageFile>();

        LineSeries throttleSeries = new LineSeries();

        LineSeries steeringSeries = new LineSeries();

        LineSeries indicatorSeries = new LineSeries();

        LinearAxis indexAxis = new LinearAxis();

        int? relocatedThrottle = null;
        int? relocatedSteering = null;

        public Form1()
        {
            InitializeComponent();

            lblText.Text = "";
            lblStickCoords.Text = "";

            plot.BackColor = Color.White;
            plot.Model = new PlotModel();
            indexAxis.Position = AxisPosition.Bottom;
            indexAxis.MajorTickSize = 20;
            indexAxis.MinorTickSize = 5;
            indexAxis.Minimum = 0;
            indexAxis.Maximum = 100;
            indexAxis.Zoom(0, 100);
            indexAxis.TickStyle = OxyPlot.Axes.TickStyle.Inside;
            plot.Model.Axes.Add(indexAxis);
            LinearAxis throttleAxis = new LinearAxis();
            OxyColor throttleColour = OxyColors.DarkGreen;
            throttleAxis.Title = "Throttle";
            throttleAxis.Position = AxisPosition.Left;
            throttleAxis.AxislineColor = throttleColour;
            throttleAxis.TextColor = throttleColour;
            throttleAxis.TicklineColor = throttleColour;
            throttleAxis.TitleColor = throttleColour;
            throttleAxis.MinorTicklineColor = throttleColour;
            throttleAxis.Minimum = -130;
            throttleAxis.Maximum = 130;
            throttleAxis.MajorTickSize = 20;
            throttleAxis.MinorTickSize = 5;
            throttleAxis.TickStyle = OxyPlot.Axes.TickStyle.Inside;
            plot.Model.Axes.Add(throttleAxis);
            LinearAxis steeringAxis = new LinearAxis();
            OxyColor steeringColour = OxyColors.Red;
            steeringAxis.Title = "Steering";
            steeringAxis.Position = AxisPosition.Right;
            steeringAxis.AxislineColor = steeringColour;
            steeringAxis.TextColor = steeringColour;
            steeringAxis.TicklineColor = steeringColour;
            steeringAxis.TitleColor = steeringColour;
            steeringAxis.MinorTicklineColor = steeringColour;
            steeringAxis.Minimum = -130;
            steeringAxis.Maximum = 130;
            steeringAxis.MajorTickSize = 20;
            steeringAxis.MinorTickSize = 5;
            steeringAxis.TickStyle = OxyPlot.Axes.TickStyle.Inside;
            plot.Model.Axes.Add(steeringAxis);

            throttleSeries.Color = throttleColour;
            steeringSeries.Color = steeringColour;

            indicatorSeries.Color = OxyColors.Pink;
            indicatorSeries.Points.Add(new DataPoint(0, -130));
            indicatorSeries.Points.Add(new DataPoint(0, 130));

            plot.Model.Series.Add(throttleSeries);
            plot.Model.Series.Add(steeringSeries);
            plot.Model.Series.Add(indicatorSeries);
        }
        private void Form1_Shown(object sender, EventArgs e)
        {
            OpenFileDialog d = new OpenFileDialog();
            d.Filter = "JPG files (*.jpg)|*.jpg|All files (*.*)|*.*";
            d.Multiselect = false;
            if (d.ShowDialog() != DialogResult.OK)
            {
                MessageBox.Show("Goodbye!");
                this.Close();
                return;
            }
            string p;
            p = Path.GetDirectoryName(d.FileName);
            DirectoryInfo di = new DirectoryInfo(p);
            FileInfo[] files = di.GetFiles("*.jpg");
            foreach (FileInfo f in files)
            {
                ImageFile nf = ImageFile.ParseFileName(f);
                if (nf != null)
                {
                    allFiles.Add(nf);
                }
            }
            allFiles.Sort((x, y) => x.SequenceNumber.CompareTo(y.SequenceNumber));

            if (allFiles.Count <= 0)
            {
                MessageBox.Show("No Valid Images! Goodbye!");
                this.Close();
                return;
            }

            SetTrackbarSize();
            AdjustPlotSpread();
            UpdateAllPlotPoints();
            ShowCurrentImage();
        }

        private void SetTrackbarSize()
        {
            trkbarPlayback.ValueChanged -= TrkbarPlayback_ValueChanged;
            int prevIdx = trkbarPlayback.Value;
            trkbarPlayback.Minimum = 0;
            trkbarPlayback.Maximum = allFiles.Count - 1;
            if (prevIdx < trkbarPlayback.Maximum)
            {
                trkbarPlayback.Value = prevIdx;
            }
            else
            {
                trkbarPlayback.Value = trkbarPlayback.Maximum;
            }
            trkbarPlayback.ValueChanged += TrkbarPlayback_ValueChanged;
        }

        private void UpdateAllPlotPointsFrom(int start)
        {
            int cnt = allFiles.Count;
            int i;
            for (i = start; i < cnt; i++)
            {
                ImageFile f = allFiles[i];
                UpdateSinglePlotPoint(i, f.Throttle, f.Steering, false);
            }
            while (throttleSeries.Points.Count > cnt)
            {
                throttleSeries.Points.RemoveAt(throttleSeries.Points.Count - 1);
            }
            while (steeringSeries.Points.Count > cnt)
            {
                steeringSeries.Points.RemoveAt(steeringSeries.Points.Count - 1);
            }
            plot.Refresh();
        }

        private void UpdateAllPlotPoints()
        {
            UpdateAllPlotPointsFrom(0);
        }

        private void UpdateSinglePlotPoint(int idx, int throttle, int steering, bool refresh)
        {
            if (idx < throttleSeries.Points.Count)
            {
                throttleSeries.Points[idx] = new DataPoint(Convert.ToDouble(idx), Convert.ToDouble(throttle));
            }
            else if (idx == throttleSeries.Points.Count)
            {
                throttleSeries.Points.Add(new DataPoint(Convert.ToDouble(idx), Convert.ToDouble(throttle)));
            }
            if (idx < steeringSeries.Points.Count)
            {
                steeringSeries.Points[idx] = new DataPoint(Convert.ToDouble(idx), Convert.ToDouble(steering));
            }
            else if (idx == steeringSeries.Points.Count)
            {
                steeringSeries.Points.Add(new DataPoint(Convert.ToDouble(idx), Convert.ToDouble(steering)));
            }
            if (refresh)
            {
                plot.Refresh();
            }
        }
        private void UpdateSinglePlotPoint(int idx, int throttle, int steering)
        {
            UpdateSinglePlotPoint(idx, throttle, steering, true);
        }

        private void ShowCurrentImage()
        {
            ImageFile f = allFiles[trkbarPlayback.Value];
            Image img;
            using (Bitmap fileContents = new Bitmap(f.FullPath))
            {
                img = new Bitmap(fileContents);
            }
            lblText.Text = f.Name;

            if (img.Width != picboxPicture.Width || img.Height != picboxPicture.Height)
            {
                Bitmap bm = ResizeImage(img, picboxPicture.Width, picboxPicture.Height);
                picboxPicture.Image = bm;
            }
            else
            {
                picboxPicture.Image = img;
            }

            DrawJoystick();

            this.Refresh();
            GC.Collect();
            GC.WaitForPendingFinalizers();
        }

        private void DrawJoystick()
        {
            ImageFile f = allFiles[trkbarPlayback.Value];

            Bitmap bm;
            bm = new Bitmap(picboxStick.Width - 1, picboxStick.Height - 1);
            Graphics g = Graphics.FromImage(bm);

            int halfWidth = bm.Width / 2;
            int halfHeight = bm.Height / 2;

            g.DrawRectangle(new Pen(Color.LightGray), 2, 2, bm.Width - 4, bm.Height - 4);
            g.DrawLine(new Pen(Color.LightGray), 0, halfHeight - 3, bm.Width, halfHeight - 3);
            g.DrawLine(new Pen(Color.LightGray), 0, halfHeight + 3, bm.Width, halfHeight + 3);
            g.DrawLine(new Pen(Color.LightGray), halfWidth - 3, 0, halfWidth - 3, bm.Height);
            g.DrawLine(new Pen(Color.LightGray), halfWidth + 3, 0, halfWidth + 3, bm.Height);

            g.DrawLine(new Pen(Color.Black), 0, halfHeight - f.Throttle, bm.Width, halfHeight - f.Throttle);
            if (f.Throttle < 128)
            {
                g.DrawLine(new Pen(Color.Black), 0, halfHeight - (f.Throttle + 1), bm.Width, halfHeight - (f.Throttle + 1));
            }
            if (f.Throttle > -128)
            {
                g.DrawLine(new Pen(Color.Black), 0, halfHeight - (f.Throttle - 1), bm.Width, halfHeight - (f.Throttle - 1));
            }

            g.DrawLine(new Pen(Color.Black), halfWidth + f.Steering, 0, halfWidth + f.Steering, bm.Height);
            if (f.Steering < 128)
            {
                g.DrawLine(new Pen(Color.Black), halfWidth + f.Steering + 1, 0, halfWidth + f.Steering + 1, bm.Height);
            }
            if (f.Steering > -128)
            {
                g.DrawLine(new Pen(Color.Black), halfWidth + f.Steering - 1, 0, halfWidth + f.Steering - 1, bm.Height);
            }

            g.DrawLine(new Pen(Color.Black), halfWidth, halfHeight, halfWidth + f.Steering, halfHeight - f.Throttle);

            if (relocatedThrottle.HasValue && relocatedSteering.HasValue)
            {
                g.DrawLine(new Pen(Color.Red), halfWidth, halfHeight, halfWidth + relocatedSteering.Value, halfHeight - relocatedThrottle.Value);
                g.DrawLine(new Pen(Color.Red), 0, halfHeight - relocatedThrottle.Value, bm.Width, halfHeight - relocatedThrottle.Value);
                g.DrawLine(new Pen(Color.Red), halfWidth + relocatedSteering.Value, 0, halfWidth + relocatedSteering.Value, bm.Height);
            }

            picboxStick.Image = bm;
        }

        private void AdjustPlotSpread()
        {
            int i = trkbarPlayback.Value;
            int lidx = i - (PLOTSPREAD / 2);
            int ridx = i + (PLOTSPREAD / 2);
            if (lidx >= 0)
            {
                plot.Model.Axes[0].Minimum = lidx;
            }
            else
            {
                plot.Model.Axes[0].Minimum = 0;
            }
            if (ridx < allFiles.Count)
            {
                plot.Model.Axes[0].Maximum = ridx;
            }
            else
            {
                plot.Model.Axes[0].Maximum = allFiles.Count;
            }
            indexAxis.Zoom(plot.Model.Axes[0].Minimum, plot.Model.Axes[0].Maximum);
            plot.Refresh();
        }

        private void TrkbarPlayback_ValueChanged(object sender, EventArgs e)
        {
            ResetRenamer();
            MovePlotIndicator();
            AdjustPlotSpread();
            ShowCurrentImage();
        }

        private void ResetRenamer()
        {
            relocatedThrottle = null;
            relocatedSteering = null;
            lblStickCoords.Text = "";
            btnRename.Enabled = false;
        }

        private void MovePlotIndicator()
        {
            indicatorSeries.Points.Clear();
            indicatorSeries.Points.Add(new DataPoint(Convert.ToDouble(trkbarPlayback.Value), -130));
            indicatorSeries.Points.Add(new DataPoint(Convert.ToDouble(trkbarPlayback.Value), 130));
        }

        private void TrkbarPlayback_KeyDown(object sender, KeyEventArgs e)
        {
            if (e.KeyCode == Keys.Delete)
            {
                BtnDelete_Click(sender, e);
                return;
            }
            TrkbarPlayback_ValueChanged(sender, e);
        }

        private void TrkbarPlayback_KeyPress(object sender, KeyPressEventArgs e)
        {
            TrkbarPlayback_ValueChanged(sender, e);
        }

        public static Bitmap ResizeImage(Image image, int width, int height)
        {
            var destRect = new Rectangle(0, 0, width, height);
            var destImage = new Bitmap(width, height);

            destImage.SetResolution(image.HorizontalResolution, image.VerticalResolution);

            using (var graphics = Graphics.FromImage(destImage))
            {
                graphics.CompositingMode = CompositingMode.SourceCopy;
                graphics.CompositingQuality = CompositingQuality.HighQuality;
                graphics.InterpolationMode = InterpolationMode.HighQualityBicubic;
                graphics.SmoothingMode = SmoothingMode.HighQuality;
                graphics.PixelOffsetMode = PixelOffsetMode.HighQuality;

                using (var wrapMode = new ImageAttributes())
                {
                    wrapMode.SetWrapMode(WrapMode.TileFlipXY);
                    graphics.DrawImage(image, destRect, 0, 0, image.Width, image.Height, GraphicsUnit.Pixel, wrapMode);
                }
            }

            return destImage;
        }

        bool stickMouseDown = false;

        private void PicboxStick_MouseClick(object sender, MouseEventArgs e)
        {
            if (stickMouseDown == false)
            {
                return;
            }
            int throttle = (picboxStick.Image.Height / 2) - e.Y;
            int steering = e.X - (picboxStick.Image.Width / 2);
            if (throttle > 110)
            {
                throttle = 110;
            }
            if (throttle < -110)
            {
                throttle = -110;
            }
            if (steering > 110)
            {
                steering = 110;
            }
            if (steering < -110)
            {
                steering = -110;
            }
            relocatedSteering = steering;
            relocatedThrottle = throttle;
            lblStickCoords.Text = string.Format("{0}  {1}", throttle, steering);
            btnRename.Enabled = true;
            DrawJoystick();
        }

        private void PicboxStick_MouseDown(object sender, MouseEventArgs e)
        {
            stickMouseDown = true;
            PicboxStick_MouseClick(sender, e);
        }

        private void PicboxStick_MouseMove(object sender, MouseEventArgs e)
        {
            PicboxStick_MouseClick(sender, e);
        }

        private void PicboxStick_MouseLeave(object sender, EventArgs e)
        {
            stickMouseDown = false;
        }

        private void PicboxStick_MouseUp(object sender, MouseEventArgs e)
        {
            stickMouseDown = false;
        }

        private void BtnRename_Click(object sender, EventArgs e)
        {
            if (relocatedSteering.HasValue == false || relocatedThrottle.HasValue == false)
            {
                return;
            }
            ImageFile f = allFiles[trkbarPlayback.Value];
            f.Rename(relocatedThrottle.Value, relocatedSteering.Value);
            UpdateSinglePlotPoint(trkbarPlayback.Value, f.Throttle, f.Steering);
            ShowCurrentImage();
        }

        private void BtnDelete_Click(object sender, EventArgs e)
        {
            ImageFile f = allFiles[trkbarPlayback.Value];
            f.Delete();
            allFiles.RemoveAt(trkbarPlayback.Value);

            ResetRenamer();
            SetTrackbarSize();
            AdjustPlotSpread();
            UpdateAllPlotPoints();
            MovePlotIndicator();
            ShowCurrentImage();
        }

        private void Plot_KeyDown(object sender, KeyEventArgs e)
        {
            if (e.KeyCode == Keys.Delete)
            {
                BtnDelete_Click(sender, e);
                return;
            }
        }

        private void Form1_KeyDown(object sender, KeyEventArgs e)
        {
            if (e.KeyCode == Keys.Delete)
            {
                BtnDelete_Click(sender, e);
                return;
            }
        }

        private void BtnDelete_KeyDown(object sender, KeyEventArgs e)
        {
            if (e.KeyCode == Keys.Delete)
            {
                BtnDelete_Click(sender, e);
                return;
            }
        }

        private void BtnRename_KeyDown(object sender, KeyEventArgs e)
        {
            if (e.KeyCode == Keys.Delete)
            {
                BtnDelete_Click(sender, e);
                return;
            }
        }
    }
}
