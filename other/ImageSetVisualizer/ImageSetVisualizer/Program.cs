using System;
using System.IO;
using System.Collections.Generic;
using System.Linq;
using System.Threading.Tasks;
using System.Windows.Forms;

namespace ImageSetVisualizer
{
    static class Program
    {
        /// <summary>
        /// The main entry point for the application.
        /// </summary>
        [STAThread]
        static void Main()
        {
            Application.EnableVisualStyles();
            Application.SetCompatibleTextRenderingDefault(false);
            Application.Run(new Form1());
        }
    }

    public class ImageFile
    {
        public enum StickMode
        {
            Default,
            Max,
            Left,
            Right,
            LTRS_Converted,
            LSRT_Converted,
            Dpad,
        };

        public const StickMode STICKMODE = StickMode.Default;
        public const int STICKMIDDLE = 127;

        private FileInfo child;

        public int SequenceNumber
        {
            get;
            private set;
        }

        public int Throttle
        {
            get;
            private set;
        }

        public int Steering
        {
            get;
            private set;
        }

        public string Name
        {
            get;
            private set;
        }

        public string FullPath
        {
            get
            {
                string fpath = Path.Combine(child.DirectoryName, this.Name) + ".jpg";
                return fpath;
            }
        }

        private ImageFile()
        {
        }

        public void Delete()
        {
            child.Delete();
        }

        public void Rename(int throttle, int steering)
        {
            string fpath = child.FullName;
            string fname = Path.GetFileNameWithoutExtension(Path.GetFileName(fpath));
            string[] parts = fname.Split('_');
            string nname = parts[0] + "_" + parts[1];

            int throttleAbs = throttle + STICKMIDDLE;
            int steeringAbs = steering + STICKMIDDLE;
            throttleAbs = throttleAbs < 0 ? 0 : (throttleAbs > 255 ? 255 : throttleAbs);
            steeringAbs = steeringAbs < 0 ? 0 : (steeringAbs > 255 ? 255 : steeringAbs);
            nname += string.Format("_{0:000}{1:000}", throttleAbs, steeringAbs);

            nname += "_" + parts[3];

            double mag = Math.Sqrt(Convert.ToDouble((throttle * throttle) + (steering * steering)));

            /*
            if (mag > 100)
            {
                mag = 100;
            }
            */

            double theta = Math.Atan2(Convert.ToDouble(steering), Convert.ToDouble(throttle));
            // double radians = Math.PI * ang / 180.0;
            double deg = theta * 180.0 / Math.PI;
            if (deg < 0.0)
            {
                deg += 360.0;
            }
            int magi = Convert.ToInt32(Math.Round(mag));
            int degi = Convert.ToInt32(Math.Round(deg));
            for (int i = 0; i < 3; i++)
            {
                nname += string.Format("_{0:000}{1:000}", magi, degi);
            }
            this.Name = nname;
            string nfpath = Path.Combine(child.DirectoryName, nname + ".jpg");
            child.MoveTo(nfpath);
            child = new FileInfo(nfpath);
            this.Throttle = throttle;
            this.Steering = steering;
        }

        public static ImageFile ParseFileName(FileInfo fnfo)
        {
            bool success = false;
            string fpath = fnfo.FullName;
            int throttle = 0;
            int steering = 0;
            ImageFile obj = new ImageFile();
            obj.child = fnfo;
            try
            {
                string fname = Path.GetFileNameWithoutExtension(Path.GetFileName(fpath));
                obj.Name = fname;
                string[] dotparts = fname.Split('.');
                string[] parts = dotparts[0].Split('_');

                obj.SequenceNumber = Convert.ToInt32(parts[1], 10);

                if (STICKMODE == StickMode.Default)
                {
                    int left_y, right_x;
                    if (DecodeThrottleSteering(parts[2], out left_y, out right_x) == false)
                    {
                        return null;
                    }
                    throttle = left_y;
                    steering = right_x;
                    success = true;
                }
                else
                {
                    double mag_left, ang_left;
                    double mag_right, ang_right;
                    double mag_dpad, ang_dpad;
                    
                    if (DecodeMagAng(parts[4], out mag_left, out ang_left) == false)
                    {
                        return null;
                    }
                    if (DecodeMagAng(parts[5], out mag_right, out ang_right) == false)
                    {
                        return null;
                    }
                    if (DecodeMagAng(parts[6], out mag_dpad, out ang_dpad) == false)
                    {
                        return null;
                    }

                    if (STICKMODE == StickMode.Max)
                    {
                        if (mag_dpad >= mag_left && mag_dpad >= mag_right)
                        {
                            ConvertVectorToDrive(mag_dpad, ang_dpad, out throttle, out steering);
                            success = true;
                        }
                        else if (mag_left >= mag_dpad && mag_left >= mag_right)
                        {
                            ConvertVectorToDrive(mag_left, ang_left, out throttle, out steering);
                            success = true;
                        }
                        else if (mag_right >= mag_dpad && mag_right >= mag_left)
                        {
                            ConvertVectorToDrive(mag_right, ang_right, out throttle, out steering);
                            success = true;
                        }
                    }
                    else if (STICKMODE == StickMode.Dpad)
                    {
                        ConvertVectorToDrive(mag_dpad, ang_dpad, out throttle, out steering);
                        success = true;
                    }
                    else if (STICKMODE == StickMode.Left)
                    {
                        ConvertVectorToDrive(mag_left, ang_left, out throttle, out steering);
                        success = true;
                    }
                    else if (STICKMODE == StickMode.Right)
                    {
                        ConvertVectorToDrive(mag_right, ang_right, out throttle, out steering);
                        success = true;
                    }
                    else if (STICKMODE == StickMode.LSRT_Converted || STICKMODE == StickMode.LTRS_Converted)
                    {
                        int lt, ls, rt, rs;
                        ConvertVectorToDrive(mag_left, ang_left, out lt, out ls);
                        ConvertVectorToDrive(mag_right, ang_right, out rt, out rs);
                        if (STICKMODE == StickMode.LSRT_Converted)
                        {
                            throttle = rt;
                            steering = ls;
                        }
                        else
                        {
                            throttle = rs;
                            steering = lt;
                        }
                        success = true;
                    }
                }
            }
            catch
            {
                return null;
            }
            if (success)
            {
                obj.Throttle = throttle; obj.Steering = steering;
                return obj;
            }
            return null;
        }

        private static bool DecodeThrottleSteering(string s, out int y, out int x)
        {
            x = 0;
            y = 0;
            try
            {
                y = Convert.ToInt32(s.Substring(0, 3));
                x = Convert.ToInt32(s.Substring(3));
                y -= STICKMIDDLE;
                x -= STICKMIDDLE;
                return true;
            }
            catch
            {
                return false;
            }
        }

        private static bool DecodeMagAng(string s, out double mag, out double ang)
        {
            mag = 0;
            ang = 0;
            try
            {
                mag = Convert.ToSingle(s.Substring(0, 3));
                ang = Convert.ToSingle(s.Substring(3));
                return true;
            }
            catch
            {
                return false;
            }
        }

        private static void ConvertVectorToDrive(double mag, double ang, out int throttle, out int steering)
        {
            double radians = Math.PI * ang / 180.0;
            throttle = Convert.ToInt32(Math.Round(mag * Math.Cos(radians)));
            steering = Convert.ToInt32(Math.Round(mag * Math.Sin(radians)));
        }
    }
}
