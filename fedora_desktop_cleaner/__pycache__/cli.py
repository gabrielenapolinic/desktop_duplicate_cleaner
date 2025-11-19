"""
Command Line Interface for fedora-desktop-cleaner
"""

import argparse
import sys
from .cleaner import DesktopDuplicateCleaner
from .exceptions import CleanerError


def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(
        description="Clean duplicate desktop applications from Fedora Linux 'Open With' dialogs",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s                    # Clean duplicates (interactive)
  %(prog)s --dry-run          # Show what would be cleaned
  %(prog)s --verbose          # Detailed output
  %(prog)s --auto             # Clean without confirmation

This tool removes annoying duplicate entries from the "Open With" dialog
by cleaning Wine extensions, hiding duplicate system applications, and 
removing duplicate MIME associations. Automatic backups are created.

Supported systems: Fedora Linux (all desktop environments)
        """
    )
    
    parser.add_argument(
        '--dry-run', '-n',
        action='store_true',
        help='Show what would be done without making changes'
    )
    
    parser.add_argument(
        '--verbose', '-v',
        action='store_true', 
        help='Show detailed output'
    )
    
    parser.add_argument(
        '--auto', '-y',
        action='store_true',
        help='Run without confirmation prompt'
    )
    
    parser.add_argument(
        '--version',
        action='version',
        version='%(prog)s 1.0.0'
    )
    
    args = parser.parse_args()
    
    # Show warning and get confirmation unless --auto is specified
    if not args.auto and not args.dry_run:
        print("🧹 Fedora Desktop Cleaner v1.0.0")
        print()
        print("This tool will clean duplicate desktop applications from your 'Open With' dialogs.")
        print("It will:")
        print("  • Remove Wine extension duplicates")  
        print("  • Hide system application duplicates")
        print("  • Clean MIME association duplicates")
        print("  • Create automatic backups")
        print()
        print("⚠️  This will modify desktop application files.")
        print("   Backups will be created automatically.")
        print()
        
        try:
            response = input("Continue? (y/N): ").lower()
            if response not in ['y', 'yes']:
                print("Operation cancelled.")
                return 0
        except KeyboardInterrupt:
            print("\nOperation cancelled.")
            return 0
    
    # Run the cleaner
    try:
        cleaner = DesktopDuplicateCleaner(
            dry_run=args.dry_run,
            verbose=args.verbose
        )
        
        stats = cleaner.run()
        
        # Show final result
        if not args.dry_run:
            print()
            print("🎉 Desktop cleanup completed!")
            print("   Right-click any file and check 'Open With' to see the results.")
            
            if stats['backups_created'] > 0:
                print(f"   {stats['backups_created']} backup(s) created with .bak extension.")
        
        return 0
        
    except CleanerError as e:
        print(f"❌ Error: {e}", file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        print("\n⚠️  Operation interrupted by user.", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"❌ Unexpected error: {e}", file=sys.stderr)
        if args.verbose:
            import traceback
            traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())